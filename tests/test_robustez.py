"""Testes de seguranca com dados sinteticos; nao executam Fortran nem make.

Os quadros constantes usados aqui nao sao resultados da equacao do telegrafista.
Todas as escritas ficam em diretorios temporarios fora dos resultados do TCC.
"""
from __future__ import annotations

import contextlib
import csv
import io
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
BATTERY = ROOT / 'arquivos-roteiro-simulacoes'
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(BATTERY))

import autoconvergencia as auto
import convergencia_caso1 as conv
import executar_caso1 as runner
import executar_casos as cases
import gerar_figuras_comparativas as figures

TMP = '/tmp/opencode' if Path('/tmp/opencode').is_dir() else None
PARAMS = (0, 0, 200, 0)


def fixture(directory: Path, n=2, params=PARAMS):
    directory.mkdir(parents=True, exist_ok=True)
    manifest = dict(id=cases.run_id(params), c=2., a=params[0], b=params[1],
                    beta=params[2], x0=params[3], num_cells=n, domain=[-2., 2.],
                    tfinal=.8, num_output_times=64, order=2, limiter=['mc']*3,
                    source_split=1, boundary=['extrap']*2)
    (directory / 'parametros.json').write_text(json.dumps(manifest))
    inputs = dict(num_dim='1', num_cells=str(n), lower='-2', upper='2',
                  num_eqn='3', num_waves='3', num_aux='0', t0='0',
                  output_style='1', num_output_times='64', tfinal='.8',
                  output_format='1', order='2', limiter='4 4 4', source_split='1',
                  num_ghost='2', bc_lower='1', bc_upper='1', capa_index='0',
                  cfl_desired='.9', cfl_max='1', dt_initial='.1', dt_max='1e99',
                  dt_variable='T', output_t0='T', use_fwaves='F')
    (directory / 'claw.data').write_text(''.join(f'{v} =: {k}\n' for k, v in inputs.items()))
    (directory / 'setprob.data').write_text(''.join(
        f'{manifest[k]} =: {k}\n' for k in ('c', 'a', 'b', 'beta', 'x0')))
    for k in range(65):
        (directory / f'fort.q{k:04d}').write_text(
            f'1 grid_number\n1 AMR_level\n{n} mx\n-2 xlow\n{4/n} dx\n\n'
            + '.5 0 0\n'*n)
        (directory / f'fort.t{k:04d}').write_text(
            f'{k*.8/64:.17g} time\n3 meqn\n1 ngrids\n0 maux\n1 ndim\n2 nghost\nascii format\n')
    with (directory / 'amplitude.csv').open('w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['frame', 't', 'A_max_abs_u'])
        w.writerows((k, k*.8/64, .5) for k in range(65))
    (directory / 'perfis.csv').write_text('frame,t,x,u,u_t,u_x\n')
    (directory / 'fort.info').write_text('info = 0\n'*64)
    return manifest


class TemporaryTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='telegraph-test-', dir=TMP)
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)


class ConvergenceTests(TemporaryTest):
    def test_factor_two_retains_original_formula(self):
        self.assertEqual(conv.ordem(.045, .018), math.log(.045/.018)/math.log(2.))

    def test_factor_four_uses_actual_spacing(self):
        self.assertEqual(conv.ordem(.04, .01, 4.), 1.)

    def test_zero_error_has_no_order(self):
        self.assertTrue(math.isnan(conv.ordem(0., .1)))

    def test_invalid_spacing_is_rejected(self):
        with self.assertRaises(ValueError):
            conv.ordem(.1, .01, 1.)

    def test_missing_requested_time_is_rejected(self):
        fixture(self.directory)
        with self.assertRaises(ValueError):
            conv.quadro_mais_proximo(self.directory, .401)

    def test_fortran_exponent_is_accepted(self):
        fixture(self.directory)
        p = self.directory / 'fort.q0000'
        p.write_text(p.read_text().replace('.5 0 0', '5.0D-1 0 0'))
        self.assertEqual(conv.ler_quadro(self.directory, 0)[3], [.5, .5])

    def test_nonfinite_state_is_rejected(self):
        fixture(self.directory)
        p = self.directory / 'fort.q0000'
        p.write_text(p.read_text().replace('.5 0 0', 'nan 0 0'))
        with self.assertRaises(ValueError):
            conv.ler_quadro(self.directory, 0)

    def test_incompatible_series_are_rejected(self):
        rows = [dict(N=n, dx=4/n, tempo=.4, c=c, beta=200, lower=-2, upper=2,
                     e_l2_u=.1, e_l2_ut=.1, e_l2_ux=.1)
                for n, c in ((128, 2), (256, 3))]
        with self.assertRaises(ValueError):
            conv.calcular_ordens(rows)

    def test_other_time_does_not_compare_against_t04(self):
        row = dict(N=128, tempo=.8, c=2., beta=200., lower=-2., upper=2.)
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(conv.conferir([row]), 0)
        self.assertIn('nao se aplica', out.getvalue())
        self.assertNotIn('DIVERGE', out.getvalue())


class BatteryTests(TemporaryTest):
    def setUp(self):
        super().setUp()
        self.manifest = fixture(self.directory)

    def test_historical_output_can_be_analysed(self):
        self.assertTrue(cases.complete(self.directory, PARAMS, 2))
        self.assertNotIn('provenance', self.manifest)

    def test_changed_physics_manifest_is_rejected(self):
        self.manifest['c'] = 99
        (self.directory / 'parametros.json').write_text(json.dumps(self.manifest))
        self.assertFalse(cases.complete(self.directory, PARAMS))

    def test_changed_effective_configuration_is_rejected(self):
        p = self.directory / 'claw.data'
        p.write_text(p.read_text().replace('2 =: order', '1 =: order'))
        self.assertFalse(cases.complete(self.directory, PARAMS))

    def test_incorrect_frame_time_is_rejected(self):
        p = self.directory / 'fort.t0032'
        p.write_text(p.read_text().replace('0.40000000000000002', '0.7'))
        self.assertFalse(cases.complete(self.directory, PARAMS))

    def test_corrupt_csv_is_rejected(self):
        p = self.directory / 'amplitude.csv'
        p.write_text(p.read_text().replace('0.5', '0.6'))
        self.assertFalse(cases.complete(self.directory, PARAMS))

    def test_malformed_manifest_returns_false(self):
        (self.directory / 'parametros.json').write_text('{')
        self.assertFalse(cases.complete(self.directory, PARAMS))

    def test_incomplete_solver_status_is_rejected(self):
        (self.directory / 'fort.info').write_text('info = 0\n'*63)
        self.assertFalse(cases.complete(self.directory, PARAMS))

    def test_unexpected_extra_frame_is_rejected(self):
        (self.directory / 'fort.q0065').write_text((self.directory / 'fort.q0064').read_text())
        self.assertFalse(cases.complete(self.directory, PARAMS))

    def test_new_checksums_detect_modified_profile(self):
        self.manifest['output_sha256'] = cases.output_checksums(self.directory)
        (self.directory / 'parametros.json').write_text(json.dumps(self.manifest))
        self.assertTrue(cases.complete(self.directory, PARAMS))
        (self.directory / 'perfis.csv').write_text('modificado')
        self.assertFalse(cases.complete(self.directory, PARAMS))

    def test_historical_output_is_not_reused_as_current_build(self):
        d = self.directory / cases.run_id(PARAMS)
        fixture(d)
        with patch.object(cases.subprocess, 'run') as execute:
            with self.assertRaisesRegex(RuntimeError, 'historica'):
                cases.simulate(Path('/virtual/xclaw'), self.directory, PARAMS, 2,
                               provenance={'source_sha256': {}, 'executable_sha256': 'novo'})
        execute.assert_not_called()
        self.assertTrue((d / 'parametros.json').is_file())

    def test_current_verified_build_can_be_reused_without_execution(self):
        d = self.directory / cases.run_id(PARAMS)
        manifest = fixture(d)
        provenance = {'source_sha256': {'fonte': 'hash'}, 'executable_sha256': 'binario'}
        manifest.update(provenance=provenance, output_sha256=cases.output_checksums(d))
        (d / 'parametros.json').write_text(json.dumps(manifest))
        with patch.object(cases.subprocess, 'run') as execute, \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cases.simulate(Path('/virtual/xclaw'), self.directory,
                                            PARAMS, 2, provenance=provenance), d)
        execute.assert_not_called()

    def test_changed_binary_cannot_reuse_previous_output(self):
        d = self.directory / cases.run_id(PARAMS)
        manifest = fixture(d)
        manifest.update(provenance={'executable_sha256': 'antigo'},
                        output_sha256=cases.output_checksums(d))
        (d / 'parametros.json').write_text(json.dumps(manifest))
        with self.assertRaises(RuntimeError):
            cases.simulate(Path('/virtual/xclaw'), self.directory, PARAMS, 2,
                           provenance={'executable_sha256': 'novo'})

    def test_provenance_includes_compiled_sources_and_python_serialization(self):
        modules = {'clawpack': SimpleNamespace(__file__='/virtual/clawpack/__init__.py'),
                   'clawpack.clawutil': SimpleNamespace(
                       data=SimpleNamespace(__file__='/virtual/clawutil/data.py'))}
        command = 'gfortran -O2 -o xclaw qinit.f90 setprob.f90 src1.f90 rp1_telegraph.f90 /virtual/classic/claw1.f'
        with patch.dict(sys.modules, modules), \
                patch.object(cases.subprocess, 'check_output', return_value=command), \
                patch.object(cases, 'digest', side_effect=lambda path: path.name):
            provenance = cases.build_provenance(Path('/virtual/xclaw'))
        self.assertEqual(provenance['executable_sha256'], 'xclaw')
        self.assertIn('/virtual/classic/claw1.f', provenance['source_sha256'])
        self.assertIn('/virtual/clawutil/data.py', provenance['source_sha256'])

    def test_different_grids_cannot_be_subtracted(self):
        with self.assertRaises(ValueError):
            figures.check_same_grid(.4, [-1., 1.], .4, [-1.5, -.5, .5, 1.5])

    def test_comparisons_reject_mixed_resolutions(self):
        other = (1, 0, 200, 0)
        fixture(self.directory / cases.run_id(PARAMS), 2)
        fixture(self.directory / cases.run_id(other), 4, other)
        with patch.object(figures, 'cases', return_value={2: [PARAMS, other]}), \
                patch.object(figures, 'complete', return_value=True), \
                patch.object(sys, 'argv', ['figuras', '--dados', str(self.directory)]), \
                contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as error:
                figures.main()
        self.assertEqual(error.exception.code, 2)
        self.assertFalse((self.directory / 'figuras_comparativas').exists())


class RunnerTests(TemporaryTest):
    def setUp(self):
        super().setUp()
        self.claw = self.directory / 'claw'
        solver = self.claw / 'riemann/src/rp1_telegraph.f90'
        solver.parent.mkdir(parents=True)
        solver.write_text('! solver sintetico, nunca executado\n')
        self.locate = patch.object(runner, 'locate_claw', return_value=self.claw)
        self.locate.start()
        self.addCleanup(self.locate.stop)

    def test_dry_run_does_not_build_or_create_destination(self):
        destination = self.directory / 'saida nova'
        with patch.object(runner.subprocess, 'run') as execute, \
                contextlib.redirect_stdout(io.StringIO()):
            runner.run(128, destination, dry_run=True)
        execute.assert_not_called()
        self.assertFalse(destination.exists())

    def test_existing_output_is_preserved(self):
        target = self.directory / 'output_malha_128'
        target.mkdir()
        (target / 'sentinela').write_text('preservar')
        with patch.object(runner.subprocess, 'run') as execute:
            with self.assertRaises(ValueError):
                runner.run(128, self.directory)
        execute.assert_not_called()
        self.assertEqual((target / 'sentinela').read_text(), 'preservar')

    def test_invalid_mesh_is_rejected_before_build(self):
        with patch.object(runner.subprocess, 'run') as execute:
            with self.assertRaises(ValueError):
                runner.run(0, self.directory)
        execute.assert_not_called()

    def test_isolated_workflow_and_plotting_never_resimulate(self):
        data = SimpleNamespace(num_cells=[2], num_output_times=64, t0=0., tfinal=.8,
                               lower=[-2.], upper=[2.])
        calls = []
        def write(out_dir):
            (Path(out_dir) / 'claw.data').write_text('entrada sintetica')
        def execute(cmd, **kwargs):
            calls.append(cmd)
            if cmd[0] == str(ROOT / 'xclaw'):
                fixture(Path(kwargs['cwd']))
            return subprocess.CompletedProcess(cmd, 0)
        source = (ROOT / 'setrun.py').read_bytes()
        with patch.object(runner, 'configure', return_value=SimpleNamespace(clawdata=data, write=write)), \
                patch.object(runner.subprocess, 'run', side_effect=execute), \
                contextlib.redirect_stdout(io.StringIO()):
            output = runner.run(2, self.directory)
        self.assertTrue((output / 'fort.q0064').is_file())
        self.assertEqual(len(calls), 3)  # make, solver ficticio, VisClaw ficticio
        self.assertEqual(sum(cmd[0] == str(ROOT / 'xclaw') for cmd in calls), 1)
        self.assertIn('plotclaw.py', calls[-1][2])
        self.assertEqual((ROOT / 'setrun.py').read_bytes(), source)

    def test_failed_solver_keeps_diagnostics_without_publishing(self):
        data = SimpleNamespace()
        def execute(cmd, **kwargs):
            if cmd[0] == str(ROOT / 'xclaw'):
                raise subprocess.CalledProcessError(1, cmd)
            return subprocess.CompletedProcess(cmd, 0)
        with patch.object(runner, 'configure', return_value=SimpleNamespace(clawdata=data, write=lambda **kw: None)), \
                patch.object(runner.subprocess, 'run', side_effect=execute), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(subprocess.CalledProcessError):
                runner.run(2, self.directory, plots=False)
        self.assertFalse((self.directory / 'output_malha_2').exists())
        self.assertEqual(len(list(self.directory.glob('.caso1-N2-*/execucao.log'))), 1)

    def test_shell_wrapper_help_works_from_another_directory(self):
        env = dict(os.environ, CLAW_PYTHON=sys.executable)
        result = subprocess.run(['bash', str(ROOT / 'rodar.sh'), '--help'],
                                cwd=self.directory, env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('--sem-plots', result.stdout)

    def test_environment_checker_reports_failure_via_exit_status(self):
        env = dict(os.environ, CLAW_PYTHON='/interpretador/inexistente', CLAW='/claw/inexistente')
        result = subprocess.run(['bash', str(ROOT / 'verificar-ambiente.sh')],
                                cwd=self.directory, env=env, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('[falta]', result.stdout)


class BranchTests(TemporaryTest):
    def test_analysis_does_not_query_or_require_branch_name(self):
        rows = [dict(p_u=.85, p_ut=2.16)]*3
        with patch.object(sys, 'argv', ['auto', '--somente-analisar', '--saida', str(self.directory)]), \
                patch.object(auto, 'analyse', return_value=rows) as analyse, \
                patch.object(auto, 'write_json'), patch.object(Path, 'write_text'), \
                patch.object(auto, 'command', side_effect=AssertionError('branch nao deve ser consultada')), \
                contextlib.redirect_stdout(io.StringIO()):
            auto.main()
        analyse.assert_called_once_with(self.directory)


if __name__ == '__main__':
    unittest.main()

subroutine src1(meqn,mbc,mx,xlower,dx,q,maux,aux,t,dt)

    ! Fonte do sistema: psi(q) = (q2, b*q1-a*q2, 0).
    ! Euler explicito simultaneo apos a etapa hiperbolica (source_split=1).
    ! Guardar q1 e q2 e essencial: as duas atualizacoes usam o mesmo estado.
    ! A CFL hiperbolica, sozinha, nao controla fontes arbitrariamente rigidas.

    implicit double precision (a-h,o-z)

    dimension q(meqn,1-mbc:mx+mbc)
    dimension aux(maux,1-mbc:mx+mbc)

    common /cparam/ c, a, b

    do i = 1,mx

        q1 = q(1,i)
        q2 = q(2,i)

        q(1,i) = q1 + dt*q2
        q(2,i) = q2 + dt*(b*q1 - a*q2)

    end do

    return
end

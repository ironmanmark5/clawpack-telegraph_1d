# Compila os fontes Classic Clawpack e as rotinas desta pasta no próprio diretório.
CLAW ?= $(abspath ../../../..)
FC = gfortran
FFLAGS ?= -O2
LIB = $(CLAW)/classic/src/1d

CLASSIC = $(addprefix $(LIB)/,setaux.f90 bc1.f b4step1.f90 driver.f90 \
  claw1ez.f claw1.f copyq1.f inlinelimiter.f90 opendatafile.f out1.f step1.f90)
LOCAL = qinit.f90 setprob.f90 src1.f90 rp1_telegraph.f90

.PHONY: all .exe clean
all: xclaw
.exe: xclaw

xclaw: $(CLASSIC) $(LOCAL)
	$(FC) $(FFLAGS) -o $@ $(CLASSIC) $(LOCAL)

clean:
	rm -f xclaw

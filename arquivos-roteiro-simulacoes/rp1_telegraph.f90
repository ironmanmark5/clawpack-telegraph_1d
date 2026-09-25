! =====================================================
subroutine rp1(maxm,meqn,mwaves,maux,mbc,mx,ql,qr,auxl,auxr,wave,s,amdq,apdq)
! =====================================================

!  Riemann solver for the 1D telegrapher equation.

!
! State variables:
!       q(1) = u
!       q(2) = u_t
!       q(3) = u_x
!
! Number of equations: 3
! Number of waves:     3


! On input, ql contains the state vector at the left edge of each cell
!           qr contains the state vector at the right edge of each cell

! On output, wave contains the waves,
!            s the speeds,
!
!            amdq = A^- Delta q,
!            apdq = A^+ Delta q,
!                   the decomposition of the flux difference
!                       f(qr(i-1)) - f(ql(i))
!                   into leftgoing and rightgoing parts respectively.
!

! Note that the i'th Riemann problem has left state qr(i-1,:)
!                                    and right state ql(i,:)
! From the basic clawpack routines, this routine is called with ql = qr


    implicit double precision (a-h,o-z)

    dimension wave(meqn, mwaves, 1-mbc:maxm+mbc)
    dimension    s(mwaves,1-mbc:maxm+mbc)
    dimension   ql(meqn, 1-mbc:maxm+mbc)
    dimension   qr(meqn, 1-mbc:maxm+mbc)
    dimension apdq(meqn, 1-mbc:maxm+mbc)
    dimension amdq(meqn, 1-mbc:maxm+mbc)

!     local arrays
!     ------------
    dimension delta(3)

!     Wave propagation speed
!     (set in setprob.f90)
    common /cparam/ c, a, b


!     # split the jump in q at each interface into waves

!     # find a1 and a2, the coefficients of the 2 eigenvectors:
    do 20 i = 2-mbc, mx+mbc
        delta(1) = ql(1,i) - qr(1,i-1)
        delta(2) = ql(2,i) - qr(2,i-1)
        delta(3) = ql(3,i) - qr(3,i-1)

	a1 = 0.5d0 * ( delta(3) + delta(2)/c )

        a2 = delta(1)

        a3 = 0.5d0 * ( delta(3) - delta(2)/c )

	! wave 1  (lambda = -c)

	wave(1,1,i) = 0.d0
	wave(2,1,i) = a1*c
	wave(3,1,i) = a1

	s(1,i) = -c


	! wave 2  (lambda = 0)

	wave(1,2,i) = a2
	wave(2,2,i) = 0.d0
	wave(3,2,i) = 0.d0

	s(2,i) = 0.d0


	! wave 3  (lambda = +c)

	wave(1,3,i) = 0.d0
	wave(2,3,i) = -a3*c
	wave(3,3,i) = a3

	s(3,i) = c

    20 END DO


!     # compute the leftgoing and rightgoing flux differences:
!          s(1,i) < 0, s(2,i) = 0, and s(3,i) > 0

    do m=1,meqn
        do i = 2-mbc, mx+mbc
          amdq(m,i) = s(1,i)*wave(m,1,i)
          apdq(m,i) = s(3,i)*wave(m,3,i)
        end do
    end do

    return
    end subroutine rp1

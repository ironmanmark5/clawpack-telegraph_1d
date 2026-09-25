subroutine setprob

    implicit none

    character*25 :: fname
    integer :: iunit
    real(kind=8) :: c, a, b, beta, x0

    common /cparam/ c, a, b
    common /cqinit/ beta, x0

    iunit = 7
    fname = 'setprob.data'

    call opendatafile(iunit, fname)

    ! Wave propagation speed
    read(7,*) c

    ! Damping coefficient
    read(7,*) a

    ! Reactive coefficient
    read(7,*) b

    ! Parameter of the initial Gaussian
    read(7,*) beta

    ! Center of the initial Gaussian
    read(7,*) x0

end subroutine setprob

subroutine qinit(meqn,mbc,mx,xlower,dx,q,maux,aux)

    ! Caso 1: q = (u, u_t, u_x), com u(x,0) = exp(-beta*x**2).
    ! Avalia os perfis nos centros como aproximacoes das medias celulares.
    ! Para dados suaves, esta inicializacao tem erro O(dx**2).
    ! Apenas celulas fisicas: as fantasmas sao preenchidas por bc1.

    implicit none

    integer, intent(in) :: meqn,mbc,mx,maux
    real(kind=8), intent(in) :: xlower,dx
    real(kind=8), intent(in) :: aux(maux,1-mbc:mx+mbc)
    real(kind=8), intent(inout) :: q(meqn,1-mbc:mx+mbc)

    integer :: i
    real(kind=8) :: beta, xcell
    common /cqinit/ beta
    do i=1,mx
        xcell = xlower + (i-0.5d0)*dx
        q(1,i) = exp(-beta*xcell**2)
        q(2,i) = 0.d0
        q(3,i) = -2.d0*beta*xcell*exp(-beta*xcell**2)
    enddo

end subroutine qinit

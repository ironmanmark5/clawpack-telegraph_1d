subroutine qinit(meqn,mbc,mx,xlower,dx,q,maux,aux)

    ! q = (u, u_t, u_x), com gaussiana centrada em x0 e u_t(x,0) = 0.
    ! Valores nos centros aproximam medias celulares com erro O(dx**2)
    ! para perfis suaves; nao sao integrais exatas das medias iniciais.
    ! As celulas fantasmas sao preenchidas pela rotina oficial bc1.

    implicit none

    integer, intent(in) :: meqn,mbc,mx,maux
    real(kind=8), intent(in) :: xlower,dx
    real(kind=8), intent(in) :: aux(maux,1-mbc:mx+mbc)
    real(kind=8), intent(inout) :: q(meqn,1-mbc:mx+mbc)

    integer :: i
    real(kind=8) :: beta, x0, xcell, z
    common /cqinit/ beta, x0

    do i=1,mx
        xcell = xlower + (i-0.5d0)*dx
        z = xcell - x0
        q(1,i) = exp(-beta*z**2)
        q(2,i) = 0.d0
        q(3,i) = -2.d0*beta*z*exp(-beta*z**2)
    enddo

end subroutine qinit

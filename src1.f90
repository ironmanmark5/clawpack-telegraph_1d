subroutine src1(meqn,mbc,mx,xlower,dx,q,maux,aux,t,dt)

    implicit double precision (a-h,o-z)

    dimension q(meqn,1-mbc:mx+mbc)
    dimension aux(maux,1-mbc:mx+mbc)

    do i = 1,mx

        q(1,i) = q(1,i) + dt*q(2,i)

    end do

    return
end

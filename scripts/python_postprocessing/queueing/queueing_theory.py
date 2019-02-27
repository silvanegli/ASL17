import numpy as np

qwt=3.47
ql=33.86

m=64
lam=23826/2
s=5.21 /1000
mu=1/s

lam=ql/qwt*1000

rho= lam/(m*mu)

print "Service Rate mu: {}".format(round(mu,2))

print "Utilization: {}".format(round(rho,2))

p0=1/(1+((m*rho)**m)/(np.math.factorial(m)*(1-rho)) + np.sum([(m*rho)**n/np.math.factorial(n) for n in range(1,m)]))
eps=((m*rho)**m)/(np.math.factorial(m)*(1-rho))*p0

nq=rho*eps/(1-rho)

print "avg. number of requests in queue: {}".format(round(nq, 0))

wq=nq/lam

print "avg. waiting time in queue: {}".format(round(wq*1000,2))

w = wq + 1/mu

print "avg. response time: {}".format(round(w*1000,2))
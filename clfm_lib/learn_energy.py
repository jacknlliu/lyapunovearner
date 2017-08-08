import sys
import numpy as np
import scipy as sp
import numpy.random as npr
import scipy.linalg as linalg

from cvxopt import solvers, matrix, spdiag, div # to solve convex problems


from .compute_energy import computeEnergy
from .. config import hyperparams

# global vars
p,x,xd,d,Vxf0['L'],Vxf0['w'],options = (None for _ in range(7))

use_convex = hyperparams['use_cvxopt']

def matVecNorm(x):
    return np.sqrt(np.sum(x**2, axis=0))

def matlength(x):
  # find the max of a numpy matrix dims
  return np.max(x.shape)


def obj(x=None, z=None):
  # This function computes the derivative of the likelihood objective function
  # w.r.t. optimization parameters.
  global p,x,xd,d,Vxf0['L'],Vxf0['w'],options

  if L == -1:
      Vxf['n']    = np.sqrt(matlength(p)/d**2)
      Vxf['d']    = d
      Vxf['P']    = p.reshape(Vxf['n']*d,Vxf['n']*d)
      Vxf['SOS']  = 1
  else:
      Vxf = shape_DS(p,d,L,options)
      
  if x is None: return 0, matrix(0.0, (Vxf['d'], Vxf['n']))

  Vx = computeEnergy(x,np.array(()), Vxf, nargout=1)
  Vdot = np.sum(Vx*xd, axis=0)  #derivative of J w.r.t. xd
  norm_Vx = np.sqrt(np.sum(Vx*Vx, axis=0))
  norm_xd = np.sqrt(np.sum(xd*xd, axis=0))
  J = Vdot /(norm_Vx * norm_xd)

  J[norm_xd==0] = 0
  J[norm_Vx==0] = 0
  J[Vdot>0]     = J[Vdot>0]**2
  J[Vdot<0]     = -w*J[Vdot<0]**2
  J = np.sum(J)
  dJ = np.array(())

  H = spdiag(2 * z[0] * )
  # translate to cvxopt-like dense matrices
  if use_convex:
    return matrix(J), matrix(dJ)
  else:
    return J, dJ

def ctr_eigenvalue(p,d,L,options):
  # This function computes the derivative of the constrains w.r.t.
  # optimization parameters.

  if L == -1: # SOS
      Vxf['d'] = d
      Vxf['n'] = np.sqrt(matlength(p)/d**2)
      Vxf['P'] = p.reshape(Vxf['n']*d,Vxf['n']*d)
      Vxf['SOS'] = 1
      c  = np.zeros(Vxf['n']*d,1)
      ceq = np.array(())
  else:
      Vxf = shape_DS(p,d,L,options)
      if L > 0:
          c  = np.zeros(((L+1)*d+(L+1)*options['optimizePriors'],1))  #+options.variableSwitch
          if options['upperBoundEigenValue']:
              ceq = np.zeros((L+1,1))
          else:
              ceq = np.array(()) # zeros(L+1,1);
      else:
          c  = np.zeros((d,1))
          ceq = (np.ravel(Vxf['P']).T).dot(np.ravel(Vxf['P'])) -2

  dc = np.array(())
  dceq = np.array(())

  if L == -1:  # SOS
      c = -np.linalg.eigVals(Vxf['P'] + Vxf['P'].T - np.eye(Vxf['n']*d)*options['tol_mat_bias'])
  else:
  #     ceq = 1;
      for k in range(L):
          lambder = np.linalg.eigVals(Vxf['P'][:,:,k+1] + Vxf['P'][:,:,k+1].T)/2;
          c[k*d+1:(k+1)*d] = -lambder + options['tol_mat_bias']
          if options['upperBoundEigenValue']:
              ceq[k+1] = 1.0 - np.sum(lambder) # + Vxf.P(:,:,k+1)'

  if L > 0 and options['optimizePriors']:
      c[(L+1)*d+1:(L+1)*d+L+1] = -Vxf['Priors']

  return c, ceq, dc, dceq


def shape_DS(p,d,L,options):

  # transforming the column of parameters into Priors, Mu, and P
  P = np.zeros((d,d,L+1))

  if L == 0:
      Priors = 1
      Mu = np.zeros((d,1))
      i_c = 1
  else:
      if options['optimizePriors']:
          Priors = p[1:L+1]
          i_c = L+1
      else:
          Priors = np.ones((L+1,1))
          i_c = 0

      Priors = Priors/np.sum(Priors)
      Mu = np.concatenate((np.zeros((d,1)), p[i_c+[0:d*L]].reshape(d,L)), axis=1)
      i_c = i_c+d*L+1

  for k in range(L):
      P[:,:,k+1] = p[(i_c+k*(d**2):i_c+(k+1)*(d**2)-1)].reshape(d,d)

  Vxf['Priors'] = Priors
  Vxf['Mu']     = Mu
  Vxf['P']      = P
  Vxf['SOS']    = 0

  return Vxf

def gmm_2_parameters(Vxf, options):
  # transforming optimization parameters into a column vector
  d = Vxf['d']
  if Vxf['L'] > 0:
      if options['optimizePriors']:
          p0 = np.vstack(( 
                           np.ravel(Vxf['Priors']), 
                           Vxf['Mu'][:,1:].reshape(Vxf['L']*d,1)
                        ))
      else:
          p0 = Vxf['Mu'][:,2:].reshape(Vxf['L']*d, 1)
  else:
      p0 = np.array(())

  for k in range(Vxf['L']):

      p0 = np.vstack((
                      p0, 
                      Vxf['P'][:,:,k+1].reshape(d**2,1)
                    ))

  return p0

def parameters_2_gmm(popt, d, L, options):
  # transforming the column of parameters into Priors, Mu, and P
  Vxf = shape_DS(popt, d, L, options);

  return Vxf


def check_options(*args):
    options = args[0] if args else None
    if (not args) or ('tol_mat_bias' not in options):
        options['tol_mat_bias'] = 1e-15
    if 'tol_stopping' not in options:
        options['tol_stopping'] = 10^-10
    if 'max_iter' not in options:
        options['max_iter'] = 1000
    if not 'display' in options:
        options['display'] = 1
    else
        options.['display'] = options['display'] > 0
    if not 'optimizePriors' in options:
        options['optimizePriors'] = True
    else
        options['optimizePriors'] = options['optimizePriors'] > 0

    if not 'upperBoundEigenValue' in options:
        options['upperBoundEigenValue'] = True
    else
        options['upperBoundEigenValue'] = options['upperBoundEigenValue'] > 0

    return options


def check_constraints(p,ctr_handle,d,L,options):
# checking if every thing goes well here. Sometimes if the parameter
# 'options['cons_penalty']' is not big enough, the constrains may be violated.
# Then this function notifies the user to increase 'options['cons_penalty']'.

  c = -ctr_handle[p]

  if L > 0:
      c_P = c[0:L*d].reshape(d,L).T
  else
      c_P = c

  idx = np.nonzero(c_P<=0)
  bool_success = True;
  if idx.size != 0
      idx = np.sort(idx);
      err = np.concatenate((np.ravel(idx), c_P[idx,:]), axis=1)
      sys.stdout.write('Error in the constraints on P!\n')
      sys.stdout.write('Eigenvalues of the P^k that violates the constraints:\n')
      sys.stdout.write(err)      
      sys.stdout.flush()
      bool_success = False;


  if L>1:
      if options['optimizePriors']:
          c_Priors = c[L*d+1:L*d+L]
          idx = c_Priors[c_Priors<0]
          if idx.size==0:
              err = np.concatenate((np.ravel(idx), c_Priors[idx]), axis=1);
              sys.stdout.write('Error in the constraints on Priors!')
              sys.stdout.write('Values of the Priors that violates the constraints:')
              sys.stdout.write(err)    
              sys.stdout.flush()
              bool_success = False;

      if matlength(c) > L*d + L:
          c_x_sw = c[L * d + L + 1]
          if c_x_sw <= 0:
              sys.stdout.write('Error in the constraints on x_sw!')
              sys.stdout.write('x_sw = %f',c_x_sw)
              bool_success = False;

  if bool_success:
      sys.stdout.write('Optimization finished successfully.')
      sys.stdout.write(' ')
      sys.stdout.write(' ')
  else:
      sys.stdout.write('Optimization did not reach to an optimal point.')
      sys.stdout.write('Some constraints were slightly violated.')
      sys.stdout.write('Re-run the optimization with different initial guess to handle this issue.')
      sys.stdout.write('Increasing the number of P could be also helpful.')
      sys.stdout.write(' ')
      sys.stdout.write(' ')


def learnEnergy(Vxf0, Data, options):
    """

    This function builds an estimate of a Lyapunov (energy) function from
    demonstrations.

     Syntax:
           [Vxf J] = learnEnergy(Vxf0,Data,options)

     to also pass a structure of desired options.

     Important NOTE: Both the demonstration data, and the model estimation
     should be in the target frame of reference. In other words, this codes
     assumes that the target is at the origin!

     Inputs -----------------------------------------------------------------

       o Vxf_0:     A structure variable representing the initial guess for the
                    energy function. Please refer to the Output variable for
                    further details about its fields.

       o Data:      A 2d x N_Total matrix containing all demonstration data points.
                    Rows 1:d corresponds to trajectories and the rows d+1:2d
                    are their first time derivatives. Each column of Data stands
                    for a datapoint. All demonstrations are put next to each other
                    along the second dimension. For example, if we have 3 demos
                    D1, D2, and D3, then the matrix Data is:
                                     Data = [[D1] [D2] [D3]]

       o options: A structure to set the optional parameters of the solver.
                  The following parameters can be set in the options:
           - .tol_mat_bias:     a very small positive scalar to avoid
                                having a zero eigen value in matrices P^l [default: 10^-15]

           - .tol_stopping:     A small positive scalar defining the stoppping
                                tolerance for the optimization solver [default: 10^-10]

           - .i_max:            maximum number of iteration for the solver [default: i_max=1000]

           - .display:          An option to control whether the algorithm
                                displays the output of each iterations [default: true]

           - .optimizePriors    This is an added feature that is not reported in the paper. In fact
                                the new CLFDM model now allows to add a prior weight to each quadratic
                                energy term. IF optimizePriors sets to false, unifrom weight is considered;
                                otherwise, it will be optimized by the sovler. [default: true]

           - .upperBoundEigenValue     This is also another added feature that is impelemnted recently.
                                       When set to true, it forces the sum of eigenvalues of each P^l
                                       matrix to be equal one. [default: true]


     Outputs ----------------------------------------------------------------

       o Vxf:      A structure variable representing the energy function. It
                   is composed of the following fields:

           - .d:       Dimension of the state space, d>0.

           - .L:       The number of asymmetric quadratic components L>=0.

           - .Priors:  1 x K array representing the prior weight of each energy
                      component. Prioris are positive scalars between 0 and 1.

           - .Mu:      Each Mu(:,i) is a vector of R^d and represent the center of
                      the energy component i. Note that by construction Mu(:,1)=0!

           - .P:       Each P(:,:,i), i=1:L+1, is a d x d positive definite matrix.
                      P(:,:,1) corresponds to the symmetric energy component P^0.
                      P^1 to P^{L+1} are asymmetric quadratic terms. Note that the
                      matrices P^i are not necessarily symmetric.

           - .w:      A positive scalar weight regulating the priority between the
                      two objectives of the opitmization. Please refer to the
                      page 7 of the paper for further information.

           - .SOS:    This is an internal variable, and is automatically set to false

       o J:      The value of the objective function at the optimized point

    ###########################################################################
    ##         Copyright (c) 2014 Mohammad Khansari, LASA Lab, EPFL,         ##
    ##          CH-1015 Lausanne, Switzerland, http://lasa.epfl.ch           ##
    ###########################################################################

    Ported to Python by Lekan Ogunmolu
            August 5, 2017
    """
    # augment undefined options by updating the options dict
    options = check_options() if not options else options = check_options(options)

    d = int(Data.shape[0]/2)  # dimension of model
    x = Data[:d,:]     # state space
    xd = Data[d:,:]    # derivatives of the state space
    Vxf0['SOS'] = False

    # Optimization
    # Transform the Lyapunov model to a vector of optimization parameters
    if Vxf0['SOS']:
        p0 = npr.randn(d*Vxf0['n'], d*Vxf0['n']);
        p0 = p0.dot(p0.T)
        p0 = np.ravel(p0)
        Vxf0['L'] = -1; # to distinguish sos from other methods
    else:
        # allocate Vxf0['P'] and Vxf0['Mu']
        Vxf0['P']   =  np.zeros(( Vxf0['d'], Vxf0['d'], Vxf0['L']+1)) # wil be 2x2x3
        Vxf0['Mu']  =  np.zeros(( Vxf0['d'], Vxf0['L']+1 ))

        for l in range(Vxf0['L']):
            Vxf0['P'][:,:,l+1] = sp.linalg.solve( Vxf0['P'][:,:,l+1], np.eye(d)) )

        # in order to set the first component to be the closest Gaussian to origin
        to_sort = matVecNorm(Vxf0['Mu'])
        idx = np.argsort(to_sort, kind='mergesort');
        Vxf0['Mu'] = Vxf0['Mu'][:,idx];
        Vxf0['P']  = Vxf0['P'][:,:,idx];
        p0 = gmm_2_parameters(Vxf0,options);

        obj_handle = @(p) obj(p,x,xd,d,Vxf0['L'],Vxf0['w'],options);
        ctr_handle = @(p) ctr_eigenvalue(p,d,Vxf0['L'],options);

        # Running the optimization
        if options['display']:
            string = 'iter'
        else:
            string = 'off'

        # Options for NLP Solvers
        optNLP = {
          'Algorithm': 'interior-point', 
          'LargeScale': 'off',
          'GradObj': 'off',
          'GradConstr': 'off',
          'DerivativeCheck': 'on',
          'Display': 'iter',
          'TolX': options.tol_stopping,
          'TolFun': options.tol_stopping,
          'TolCon': 1e-12,
          'MaxFunEval': 200000,
          'MaxIter': options.max_iter,
          'DiffMinChange': 1e-4,
          'Hessian',: 'off',
          'display': string,
            }

        e = np.array(())

        """
          popt is value of minimization
          J is value of cost at the optimal solution
        """ 
        popt, J = fmincon(obj_handle, p0, ctr_handle, optNLP, e, e, e, e, e, e )
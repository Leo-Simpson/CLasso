from time import time
import numpy as np
import matplotlib.pyplot as plt

from CLasso.misc_functions import rescale, theoretical_lam, min_LS, affichage
from CLasso.compact_func import Classo, pathlasso
from CLasso.cross_validation import CV
from CLasso.stability_selection import stability, selected_param
import matplotlib.patches as mpatches


class classo_data:
    ''' Class containing the data of the problem

    Args:
        X (ndarray): Matrix representing the data of the problem
        y (ndarray): Vector representing the output of the problem
        C (str or array, optional ): Matrix of constraints to the problem. If it is 'zero-sum' then the corresponding attribute will be all-one matrix.
        rescale (bool, optional): if True, then the function :func:`rescale` will be applied to data when solving the problem

    Attributes:
        X (ndarray): Matrix representing the data of the problem
        y (ndarray): Vector representing the output of the problem
        C (str or array, optional ): Matrix of constraints to the problem. If it is 'zero-sum' then the corresponding attribute will be all-one matrix.
        rescale (bool, optional): if True, then the function :func:`rescale` will be applied to data when solving the problem

    '''
    def __init__(self, X, y, C, rescale=False):
        self.rescale = rescale  # booleen to know if we rescale the matrices
        self.X,self.y,self.C = y = X, y,C
        if type(C) == str: self.C = np.ones((1, len(X[0])))

class classo_formulation:
    ''' Class containing the data of the problem

    Attributes:
        huber (bool) : True if the formulation of the problem should be robust
            Default value = False

        concomitant (bool) : True if the formulation of the problem should be with an M-estimation of sigma.
            Default value = True

        classification (bool) : True if the formulation of the problem should be classification (if yes, then it will not be concomitant)
            Default value = False

        rho (float) : Value of rho for robust problem.
            Default value = 1.345

        rho_classification (float) : value of rho for huberized hinge loss function for classification (this parameter has to be negative).
            Default value = -1.

        e (float or string)  : value of e in concomitant formulation.
            If 'n/2' then it becomes n/2 during the method solve(), same for 'n'.
            Default value : 'n' if huber formulation ; 'n/2' else


    '''
    def __init__(self):
        self.huber = False
        self.concomitant = True
        self.classification = False
        self.rho = 1.345
        self.rho_classification = -1.
        self.e = 'not specified'

    def name(self):
        if self.huber:
            if self.classification:
                return ('Huber_Classification')
            else:
                if self.concomitant:
                    return ('Concomitant_Huber')
                else:
                    return ('Huber')
        else:
            if self.classification:
                return ('Classification')
            else:
                if self.concomitant:
                    return ('Concomitant')
                else:
                    return ('LS')

    def __repr__(self):
        return (self.name())

class classo_model_selection:
    ''' Class containing the data of the problem

    Attributes:
        PATH (bool): True if path should be computed.
            Default Value = False

        PATHparameters (PATHparameters): object parameters to compute the lasso-path.


        CV (bool):  True if Cross Validation should be computed.
            Default Value = False

        CVparameters (CVparameters):  object parameters to compute the cross-validation.


        StabSel (boolean):  True if Stability Selection should be computed.
            Default Value = True

        StabSelparameters (StabSelparameters):  object parameters to compute the stability selection.

        LAMfixed (boolean):  True if solution for a fixed lambda should be computed.
            Default Value = False

        LAMfixedparameters (LAMparameters):  object parameters to compute the lasso for a fixed lambda

    '''
    def __init__(self):

        # Model selection variables

        self.PATH = False
        self.PATHparameters = PATHparameters()

        self.CV = False
        self.CVparameters = CVparameters()

        self.StabSel = True            # Only model selection that is used by default
        self.StabSelparameters = StabSelparameters()

        self.LAMfixed = False
        self.LAMfixedparameters = LAMfixedparameters()

    def __repr__(self):
        string = ''
        if self.PATH: string += 'Path,  '
        if self.CV: string += 'Cross Validation,  '
        if self.StabSel: string += 'Stability selection, '
        if self.LAMfixed: string += 'Lambda fixed'
        return string

class PATHparameters:
    '''object parameters to compute the lasso-path.

    Attributes:
        numerical_method (str) : name of the numerical method that is used, it can be :
            'Path-Alg' (path algorithm) , 'P-PDS' (Projected primal-dual splitting method) , 'PF-PDS' (Projection-free primal-dual splitting method) or 'DR' (Douglas-Rachford-type splitting method)
            Default value : 'choose', which means that the function :func:`choose_numerical_method` will choose it accordingly to the formulation

        n_active (int or bool): if it is an integer, then the algo stop computing the path when n_active variables are actives. then the solution does not change from this point.
            Dafault value : False

        lambdas (numpy.ndarray) : list of lambdas for computinf lasso-path for cross validation on lambda.
            Default value : np.array([10**(-delta * float(i) / nlam) for i in range(0,nlam) ] ) with delta=2. and nlam = 40

        plot_sigma :
    '''
    def __init__(self):
        self.formulation = 'not specified'
        self.numerical_method = 'choose'
        self.n_active = False
        delta= 2.
        nlam = 40
        self.lambdas = np.array([10**(-delta * float(i) / nlam) for i in range(0,nlam) ] )
        self.plot_sigma = True

    def __repr__(self): return ('Npath = ' + str(len(self.lambdas))
                                + '  n_active = ' + str(self.n_active)
                                + '  lamin = ' + str(self.lambdas[-1])
                                + ';  numerical_method = ' + str(self.numerical_method))
class CVparameters:
    '''object parameters to compute the cross-validation.

    Attributes:
        seed (bool or int, optional) : Seed for random values, for an equal seed, the result will be the same. If set to False/None: pseudo-random vectors
            Default value : None

        numerical_method (str) : name of the numerical method that is used, can be :
            'Path-Alg' (path algorithm) , 'P-PDS' (Projected primal-dual splitting method) , 'PF-PDS' (Projection-free primal-dual splitting method) or 'DR' (Douglas-Rachford-type splitting method)
            Default value : 'choose', which means that the function :func:`choose_numerical_method` will choose it accordingly to the formulation

        lambdas (numpy.ndarray) : list of lambdas for computinf lasso-path for cross validation on lambda.
            Default value : np.linspace(1., 1e-3, 500)

        oneSE (bool) : if set to True, the selected lambda if computed with method 'one-standard-error'
            Default value : True

        Nsubsets (int): number of subset in the cross validation method
            Dafault value : 5

    '''
    def __init__(self):
        self.seed = None
        self.formulation = 'not specified'
        self.numerical_method = 'choose'

        self.Nsubset = 5  # Number of subsets used
        self.lambdas = np.linspace(1., 1e-3, 500)
        self.oneSE = True

    def __repr__(self): return ('Nsubset = ' + str(self.Nsubset)
                                + '  lamin = ' + str(self.lambdas[-1])
                                + '  n_lam = ' + str(len(self.lambdas))
                                + ';  numerical_method = ' + str(self.numerical_method))
class StabSelparameters:
    '''object parameters to compute the stability selection.

    Attributes:

        seed (bool or int, optional) : Seed for random values, for an equal seed, the result will be the same. If set to False/None: pseudo-random vectors
            Default value : None

        numerical_method (str) : name of the numerical method that is used, can be :
            'Path-Alg' (path algorithm) , 'P-PDS' (Projected primal-dual splitting method) , 'PF-PDS' (Projection-free primal-dual splitting method) or 'DR' (Douglas-Rachford-type splitting method)
            Default value : 'choose', which means that the function :func:`choose_numerical_method` will choose it accordingly to the formulation

        lam (float or str) : (only used if :obj:`method` = 'lam') lam for which the lasso should be computed.
            Default value : 'theoretical' which mean it will be equal to :obj:`theoretical_lam` once it is computed

        true_lam (bool) : (only used if :obj:`method` = 'lam') True if the lambda given is the real lambda, False if it lambda/lambdamax which is between 0 and 1.
            If True and lam = 'theoretical' , then it will takes the  value n*theoretical_lam.
            Default value : True


        theoretical_lam (float) : (only used if :obj:`method` = 'lam') Theoretical lam.
            Default value : 0.0 (once it is not computed yet, it is computed thanks to the function :func:`theoretical_lam` used in :meth:`classo_problem.solve`)


        method (str) : 'first', 'lam' or 'max' depending on the type of stability selection we do.
            Default value : 'first'

        B (int) : number of subsample considered.
            Default value : 50

        q (int) : number of selected variable per subsample.
            Default value : 10

        percent_nS (float) : size of subsample relatively to the total amount of sample
            Default value : 0.5

        lamin (float) : lamin when computing the lasso-path for method 'max'
            Default value : 1e-2

        hd (bool) : if set to True, then the 'max' will stop when it reaches n-k actives variables
            Default value : False

        threshold (float) : threhold for stability selection
            Default value : 0.7

        threshold_label (float) : threshold to know when the label should be plot on the graph.
            Default value : 0.4

    '''
    def __init__(self):
        self.seed = None
        self.formulation = 'not specified'
        self.numerical_method = 'choose'

        self.method = 'first'  # Can be 'first' ; 'max' or 'lam'
        self.B = 50
        self.q = 10
        self.percent_nS = 0.5
        self.lamin = 1e-2  # the lambda where one stop for 'max' method
        self.hd = False  # if set to True, then the 'max' will stop when it reaches n-k actives variables
        self.lam = 'theoretical'  # can also be a float, for the 'lam' method
        self.true_lam = True
        self.threshold = 0.7
        self.threshold_label = 0.4
        self.theoretical_lam = 0.0

    def __repr__(self): return ('method = ' + str(self.method)
                                + ';  lamin = ' + str(self.lamin)
                                + ';  lam = ' + str(self.lam)
                                + ';  B = ' + str(self.B)
                                + ';  q = ' + str(self.q)
                                + ';  percent_nS = ' + str(self.percent_nS)
                                + ';  threshold = ' + str(self.threshold)
                                + ';  numerical_method = ' + str(self.numerical_method))
class LAMfixedparameters:
            '''object parameters to compute the lasso for a fixed lambda

            Attributes:
                numerical_method (str) : name of the numerical method that is used, can be :
                    'Path-Alg' (path algorithm) , 'P-PDS' (Projected primal-dual splitting method) , 'PF-PDS' (Projection-free primal-dual splitting method) or 'DR' (Douglas-Rachford-type splitting method)
                    Default value : 'choose', which means that the function :func:`choose_numerical_method` will choose it accordingly to the formulation

                lam (float or str) : lam for which the lasso should be computed.
                    Default value : 'theoretical' which mean it will be equal to :obj:`theoretical_lam` once it is computed

                true_lam (bool) : True if the lambda given is the real lambda, False if it lambda/lambdamax which is between 0 and 1.
                    If True and lam = 'theoretical' , then it will takes the  value n*theoretical_lam.
                    Default value : True


                theoretical_lam (float) : Theoretical lam
                    Default value : 0.0 (once it is not computed yet, it is computed thanks to the function :func:`theoretical_lam` used in :meth:`classo_problem.solve`)
            '''
            def __init__(self):
                self.lam = 'theoretical'
                self.formulation = 'not specified'
                self.numerical_method = 'choose'
                self.true_lam = True
                self.theoretical_lam = 0.0

            def __repr__(self): return ('lam = ' + str(self.lam)
                                        + ';  theoretical_lam = ' + str(round(self.theoretical_lam, 4))
                                        + ';  numerical_method = ' + str(self.numerical_method))

class classo_problem:
    ''' Class that contains all the information about the problem

    Args:
        X (ndarray): Matrix representing the data of the problem
        y (ndarray): Vector representing the output of the problem
        C (str or ndarray, optional ): Matrix of constraints to the problem. If it is 'zero-sum' then the corresponding attribute will be all-one matrix.
               Default value to 'zero-sum'
        rescale (bool, optional): if True, then the function :func:`rescale` will be applied to data when solving the problem.
               Default value is 'False'

    Attributes:
        label (list or bool) : list of the labels of each variable. If set to False then there is no label
        data (classo_data) :  object containing the data of the problem.
        formulation (classo_formulation) : object containing the info about the formulation of the minimization problem we solve.
        model_selection (classo_model_selection) : object giving the parameters we need to do variable selection.
        solution (classo_solution) : object giving caracteristics of the solution of the model_selection that is asked.
                                      Before using the method solve() , its componant are empty/null.

    '''
    def __init__(self, X, y, C='zero-sum', labels=False):  # zero sum constraint by default, but it can be any matrix
        global label
        label = labels
        self.label = label
        self.data = classo_data(X, y, C)
        self.formulation = classo_formulation()
        self.model_selection = classo_model_selection()
        self.solution = classo_solution()


    # This method is the way to solve the model selections contained in the object model_selection, with the formulation of 'formulation' and the data.
    def solve(self):
        ''' Method that solve every model required in the attributes of the problem and update the attribute :obj:`problem.solution` with the characteristics of the solution.
        '''
        data = self.data
        matrices = (data.X, data.C, data.y)
        solution = classo_solution()
        n, d = len(data.X), len(data.X[0])
        if (self.formulation.e == 'n/2'): self.formulation.e = n/2  #useful to be able to write e='n/2' as it is in the default parameters
        elif(self.formulation.e == 'n'): self.formulation.e = n     # same
        elif(self.formulation.e == 'not specified'):
            if (self.formulation.huber): self.formulation.e = n
            else                       : self.formulation.e = n / 2

        if data.rescale:
            matrices, data.scaling = rescale(matrices)  # SCALING contains  :
            # (list of initial norms of A-colomns,
            #         initial norm of centered y,
            #          mean of initial y )

        # Compute the path thanks to the class solution_path which contains directely the computation in the initialisation
        if self.model_selection.PATH:
            solution.PATH = solution_PATH(matrices, self.model_selection.PATHparameters, self.formulation)

        # Compute the cross validation thanks to the class solution_CV which contains directely the computation in the initialisation
        if self.model_selection.CV:
            solution.CV = solution_CV(matrices, self.model_selection.CVparameters, self.formulation)

        # Compute the Stability Selection thanks to the class solution_SS which contains directely the computation in the initialisation
        if self.model_selection.StabSel:
            param = self.model_selection.StabSelparameters
            param.theoretical_lam = theoretical_lam(int(n * param.percent_nS), d)
            if(param.true_lam): param.theoretical_lam = param.theoretical_lam*int(n * param.percent_nS)

            solution.StabSel = solution_StabSel(matrices, param, self.formulation)

        # Compute the c-lasso problem at a fixed lam thanks to the class solution_LAMfixed which contains directely the computation in the initialisation
        if self.model_selection.LAMfixed:
            param = self.model_selection.LAMfixedparameters
            param.theoretical_lam = theoretical_lam(n, d)
            if(param.true_lam): param.theoretical_lam = param.theoretical_lam*n
            solution.LAMfixed = solution_LAMfixed(matrices, param, self.formulation)

        self.solution = solution

    def __repr__(self):
        print_parameters = ''
        if (self.model_selection.CV):
            print_parameters += '\n \nCROSS VALIDATION PARAMETERS: ' + self.model_selection.CVparameters.__repr__()
        if (self.model_selection.StabSel):
            print_parameters += '\n \nSTABILITY SELECTION PARAMETERS: ' + self.model_selection.StabSelparameters.__repr__()
        if (self.model_selection.LAMfixed):
            print_parameters += '\n \nLAMBDA FIXED PARAMETERS: ' + self.model_selection.LAMfixedparameters.__repr__()

        if (self.model_selection.PATH):
            print_parameters += '\n \nPATH PARAMETERS: ' + self.model_selection.PATHparameters.__repr__()

        return (' \n \nFORMULATION : ' + self.formulation.__repr__()
                + '\n \n' +
                'MODEL SELECTION COMPUTED :  ' + self.model_selection.__repr__()
                + print_parameters + '\n'
                )


class classo_solution:
    ''' Class giving characteristics of the solution of the model_selection that is asked.
                                      Before using the method solve() , its componant are empty/null.


    Attributes:
        PATH (solution_PATH): Solution components of the model PATH
        CV (solution_CV):  Solution components of the model CV
        StabelSel (solution_StabSel): Solution components of the model StabSel
        LAMfixed (solution_LAMfixed): Solution components of the model LAMfixed

    '''
    def __init__(self):
        self.PATH = 'not computed' #this will be filled with an object of the class 'solution_PATH' when the method solve() will be used.
        self.CV = 'not computed'  # will be an object of the class 'solution_PATH'
        self.StabSel = 'not computed' # will be an object of the class 'solution_StabSel'
        self.LAMfixed = 'not computed'

    def __repr__(self):
        return ("Running time : " + '\n'
                                 'Running time for Path computation    : ' + self.PATH.__repr__() + '\n'
                + 'Running time for Cross Validation    : ' + self.CV.__repr__() + '\n'
                + 'Running time for Stability Selection : ' + self.StabSel.__repr__() + '\n'
                + 'Running time for Fixed LAM           : ' + self.LAMfixed.__repr__()
                )


#Here, the main function used is pathlasso ; from the file compact_func
class solution_PATH:
    ''' Class giving characteristics of the solution of the model_selection that is asked.
                                      Before using the method solve() , its componant are empty/null.


    Attributes:
        PATH (solution_PATH): Solution components of the model PATH
        CV (solution_CV):  Solution components of the model CV
        StabelSel (solution_StabSel): Solution components of the model StabSel
        LAMfixed (solution_LAMfixed): Solution components of the model LAMfixed

    '''
    def __init__(self, matrices, param, formulation):
        t0 = time()

        # Formulation choosing
        if param.formulation == 'not specified': param.formulation = formulation
        name_formulation = param.formulation.name()
        rho = param.formulation.rho
        rho_classification = param.formulation.rho_classification
        e = param.formulation.e
        # Algorithmic method choosing
        numerical_method = choose_numerical_method(param.numerical_method, 'PATH', param.formulation)
        param.numerical_method = numerical_method
        # Compute the solution and is the formulation is concomitant, it also compute sigma

        out = pathlasso(matrices, lambdas=param.lambdas, n_active=param.n_active,
                                                typ=name_formulation, meth=numerical_method, return_sigm=True,
                                                rho=rho, e=e,rho_classification=rho_classification)
        if(formulation.concomitant): self.BETAS, self.LAMBDAS, self.SIGMAS = out
        else :
            self.BETAS, self.LAMBDAS = out
            self.SIGMAS = 'not computed'

        self.formulation = formulation
        self.plot_sigma = param.plot_sigma
        self.method = numerical_method
        self.save = False
        self.time = time() - t0

    def __repr__(self):
        affichage(self.BETAS, self.LAMBDAS, labels=label,
                  title=self.formulation.name() + ' Path for the method ' + self.method)
        if (type(self.save) == str): plt.savefig(self.save + 'Beta-path')
        plt.show()
        if(type(self.SIGMAS)!=str and self.plot_sigma):
            plt.plot(self.LAMBDAS, self.SIGMAS), plt.ylabel("sigma/sigMAX"), plt.xlabel("lambda")
            plt.title('Sigma for ' + self.formulation.name())
            if (type(self.save)==str) : plt.savefig(self.save + 'Sigma-path')
            plt.show()
        return (str(round(self.time, 3)) + "s")

#Here, the main function used is CV ; from the file cross_validation
class solution_CV:
    ''' Class giving characteristics of the solution of the model_selection that is asked.
                                      Before using the method solve() , its componant are empty/null.


    Attributes:
        PATH (solution_PATH): Solution components of the model PATH
        CV (solution_CV):  Solution components of the model CV
        StabelSel (solution_StabSel): Solution components of the model StabSel
        LAMfixed (solution_LAMfixed): Solution components of the model LAMfixed

    '''
    def __init__(self, matrices, param, formulation):
        t0 = time()

        # Formulation choosing
        if param.formulation == 'not specified': param.formulation = formulation
        name_formulation = param.formulation.name()

        rho = param.formulation.rho
        rho_classification = param.formulation.rho_classification
        e = param.formulation.e
        # Algorithmic method choosing
        numerical_method = choose_numerical_method(param.numerical_method, 'CV', param.formulation)
        param.numerical_method = numerical_method

        # Compute the solution and is the formulation is concomitant, it also compute sigma
        out, self.yGraph, self.standard_error, self.index_min, self.index_1SE = CV(matrices, param.Nsubset,
                                                                                   typ=name_formulation,
                                                                                   num_meth=numerical_method,
                                                                                   lambdas=param.lambdas,
                                                                                   seed=param.seed, rho=rho,
                                                                                   rho_classification=rho_classification,
                                                                                   oneSE=param.oneSE, e=e)

        self.xGraph = param.lambdas

        if param.formulation.concomitant:
            self.beta, self.sigma = out
        else:
            self.beta = out

        self.selected_param = abs(self.beta) > 1e-3  # boolean array, false iff beta_i =0
        self.refit = min_LS(matrices, self.selected_param)
        self.time = time() - t0
        self.save=False

    def __repr__(self):
        plt.bar(range(len(self.refit)), self.refit), plt.title("Cross Validation refit")
        if(type(self.save)==str): plt.savefig(self.save)
        plt.show()
        return (str(round(self.time, 3)) + "s")

    def graphic(self, mse_max=1.,save=False):
        i_min, i_1SE = self.index_min, self.index_1SE
        for j in range(len(self.xGraph)):
            if (self.yGraph[j] < mse_max): break

        plt.errorbar(self.xGraph[j:], self.yGraph[j:], self.standard_error[j:], label='mean over the k groups of data')
        plt.axvline(x=self.xGraph[i_min], color='k', label='lam with min MSE')
        plt.axvline(x=self.xGraph[i_1SE],color='r',label='lam with 1SE')
        plt.ylabel('mean of residual over lambda'), plt.xlabel('lam')
        plt.legend(), plt.title("Selection of lambda with Cross Validation")
        if(type(save)==str) : plt.savefig(save)
        plt.show()

#Here, the main function used is stability ; from the file stability selection
class solution_StabSel:
    ''' Class giving characteristics of the solution of the model_selection that is asked.
                                      Before using the method solve() , its componant are empty/null.


    Attributes:
        PATH (solution_PATH): Solution components of the model PATH
        CV (solution_CV):  Solution components of the model CV
        StabelSel (solution_StabSel): Solution components of the model StabSel
        LAMfixed (solution_LAMfixed): Solution components of the model LAMfixed

    '''
    def __init__(self, matrices, param, formulation):
        t0 = time()

        # Formulation choosing
        if param.formulation == 'not specified': param.formulation = formulation
        name_formulation = param.formulation.name()

        rho = param.formulation.rho
        rho_classification = param.formulation.rho_classification
        e = param.formulation.e
        # Compute the theoretical lam if necessary
        if param.lam == 'theoretical':
            lam = param.theoretical_lam
        else:
            lam = param.lam

        # Algorithmic method choosing
        numerical_method = choose_numerical_method(param.numerical_method, 'StabSel', param.formulation,
                                                   StabSelmethod=param.method, lam=lam)
        param.numerical_method = numerical_method

        # Compute the distribution
        output = stability(matrices, StabSelmethod=param.method, numerical_method=numerical_method,
                           lam=lam, q=param.q, B=param.B, percent_nS=param.percent_nS,
                           formulation=name_formulation, seed=param.seed, rho=rho,
                           rho_classification=rho_classification,
                           true_lam=param.true_lam, e=e)

        if (param.method == 'first'):
            distribution, distribution_path, lambdas = output
        else:
            distribution, distribution_path, lambdas = output, 'not computed', 'not used'

        self.distribution = distribution
        self.distribution_path = distribution_path
        self.lambdas_path = lambdas
        self.selected_param,self.to_label = selected_param(self.distribution, param.threshold,param.threshold_label)
        self.threshold = param.threshold
        self.refit = min_LS(matrices, self.selected_param)
        self.save1 = False
        self.save2 = False
        self.save3 = False
        self.time = time() - t0

    def __repr__(self):

        D = self.distribution
        Dpath = self.distribution_path
        selected = self.selected_param
        unselected = [not i for i in selected]
        Dselected = np.zeros(len(D))
        Dunselected = np.zeros(len(D))
        Dselected[selected] = D[selected]
        Dunselected[unselected] = D[unselected]
        plt.bar(range(len(Dselected)), Dselected, color='r', label='selected variables')
        plt.bar(range(len(Dunselected)), Dunselected, color='b', label='unselected variables')
        plt.axhline(y=self.threshold, color='g',label='threshold')
        if (type(label) != bool): plt.xticks(self.to_label, label[self.to_label], rotation=30)
        plt.legend(), plt.title("Distribution of Stability Selection")
        if (type(self.save1) == str): plt.savefig(self.save1)
        plt.show()
        print("SELECTED VARIABLES : ")
        if (type(label) != bool):
            for i in range(len(D)):
                if (selected[i]): print(i, label[i])
        else:
            for i in range(len(D)):
                if (selected[i]): print(i)

        if (type(Dpath) != str):
            lambdas = self.lambdas_path
            N = len(lambdas)
            for i in range(len(selected)):
                if selected[i]:
                    plt.plot(lambdas, [Dpath[j][i] for j in range(N)], 'r', label='selected variables')
                else:
                    plt.plot(lambdas, [Dpath[j][i] for j in range(N)], 'b', label='unselected variables')
            p1, p2 = mpatches.Patch(color='red', label='selected variables'), mpatches.Patch(color='blue',
                                                                                              label='unselected variables')
            plt.legend(handles=[p1, p2])
            plt.axhline(y=self.threshold,color='g')
            plt.title("Distribution of probability of apparence as a function of lambda")
            if (type(self.save2)==str):plt.savefig(self.save2)
            plt.show()

        plt.bar(range(len(self.refit)), self.refit)
        plt.title("Solution for Stability Selection with refit")
        if (type(self.save3) == str): plt.savefig(self.save3)
        plt.show()
        return (str(round(self.time, 3)) + "s")

#Here, the main function used is Classo ; from the file compact_func
class solution_LAMfixed:
    ''' Class giving characteristics of the solution of the model_selection that is asked.
                                      Before using the method solve() , its componant are empty/null.


    Attributes:
        PATH (solution_PATH): Solution components of the model PATH
        CV (solution_CV):  Solution components of the model CV
        StabelSel (solution_StabSel): Solution components of the model StabSel
        LAMfixed (solution_LAMfixed): Solution components of the model LAMfixed

    '''
    def __init__(self, matrices, param, formulation):
        t0 = time()
        self.formulation = formulation
        # Formulation choosing
        if param.formulation == 'not specified': param.formulation = formulation
        name_formulation = param.formulation.name()

        rho = param.formulation.rho
        rho_classification = param.formulation.rho_classification
        e = param.formulation.e
        # Compute the theoretical lam if necessary
        if param.lam == 'theoretical':
            lam = param.theoretical_lam
        else:
            lam = param.lam

        # Algorithmic method choosing
        numerical_method = choose_numerical_method(param.numerical_method, 'LAM', param.formulation, lam=lam)
        param.numerical_method = numerical_method

        # Compute the solution and is the formulation is concomitant, it also compute sigma
        out = Classo(
            matrices, lam, typ=name_formulation, meth=numerical_method, rho=rho,
            get_lambdamax=True, true_lam=param.true_lam, e=e, rho_classification=rho_classification)

        if param.formulation.concomitant: self.lambdamax, self.beta, self.sigma = out
        else: self.lambdamax, self.beta = out
        self.selected_param = abs(self.beta) > 1e-3
        self.refit = min_LS(matrices, self.selected_param)
        self.time = time() - t0
        self.save = False

    def __repr__(self):
        plt.bar(range(len(self.refit)), self.refit), plt.title("Solution for a fixed lambda with refit")
        if(type(self.save)==str): plt.savefig(self.save)
        plt.show()
        if(self.formulation.concomitant) : print("SIGMA FOR LAMFIXED  : ", self.sigma )
        return (str(round(self.time, 3)) + "s")


'''
    PATH (type : solution_PATH): object with as attributes :
        BETAS
        SIGMAS
        LAMBDAS
        method
        save
        formulation
        time

    CV (type : solution_CV): object with as attributes :
        beta
        sigma
        xGraph
        yGraph
        standard_error
        index_min
        index_1SE
        selected_param
        refit
        formulation
        time

    StabSel (type : solution_StabSel) : object with as attributes :
        distribution
        lambdas_path
        selected_param
        to_label
        refit
        formulation
        time

    LAMfixed (type : solution_LAMfixed) : object with as attributes :
        beta
        sigma
        lambdamax
        selected_param
        refit
        formulation
        time
'''





def choose_numerical_method(method, model, formulation, StabSelmethod=None, lam=None):
    ''' Annex function in order to choose the right numerical method, if the given one is invalid

    Args:
        method (str) :
        model (str) :
        formulation (classo_formulation) :
        StabSelmethod (str, optional) :
        lam (float, optional) :

    Returns :
        str : method that should be used.

    '''

    if (formulation.classification): return ('Path-Alg')

    # cases where we use classo at a fixed lambda    
    elif (model == 'LAM') or (model == 'StabSel' and StabSelmethod == 'lam'):

        if formulation.concomitant:
            if not method in ['Path-Alg', 'DR']:
                if (lam > 0.05):
                    return 'Path-Alg'
                else:
                    return 'DR'

        else:
            if not method in ['Path-Alg', 'DR', 'P-PDS', 'PF-PDS']:
                if (lam > 0.1):
                    return 'Path-Alg'
                else:
                    return 'DR'



    # cases where we use pathlasso
    else:
        if formulation.classification:
            if not method in ['Path-Alg', 'DR', 'P-PDS']: return 'Path-Alg'

        elif formulation.concomitant:
            if not method in ['Path-Alg', 'DR']: return 'Path-Alg'

        else:
            if not method in ['Path-Alg', 'DR', 'P-PDS', 'PF-PDS']: return 'Path-Alg'

    return method

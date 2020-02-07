from time import time
import numpy as np
import matplotlib.pyplot as plt

from CLasso.little_functions import rescale, theoritical_lam, min_LS, affichage
from CLasso.compact_func import Classo, pathlasso
from CLasso.cross_validation import CV
from CLasso.stability_selection import stability, selected_param
import matplotlib.patches as mpatches

'''
We build a class called classo_problem, that will contains all the information about the problem, settled in other objects : 
       - data : the matrices X, C, y to solve a problem of type y = X beta + sigma.epsilon under the constraint C.beta = 0
        
       - problem formulation : to know the formulation of the problem, robust ?  ; Jointly estimate sigma (Concomitant) ? , classification ? Default parameter is only concomitant
       
       - model selection : Path computation ; Cross Validation ; stability selection ; or Lasso problem for a fixed lambda. also contains the parameters of each of those model selection
       
       - solution : once we used the method .solve() , this componant will be added, with the solutions of the model-selections selected, with respect to the problem formulation selected

The method __repr__ allows to print this object in a way that it prints the important informations about what we are solving. 

The class of 'model selection' is defined inside the class 'problem' because we will never use it outside the class. 
'''

class classo_data:
    def __init__(self, X, y, C):
        self.rescale = False  # booleen to know if we rescale the matrices
        self.X,self.y,self.C = y = X, y,C
        if type(C) == str: self.C = np.ones((1, len(X[0])))

class classo_problem:
    global label #label will stay global, it is more easy because there is plenty of part of the code where it is used

    def __init__(self, X=np.zeros((2, 2)), y=np.zeros(2), C='zero-sum', labels=False):  # zero sum constraint by default, but it can be any matrix
        global label
        label = labels
        self.label = label

        self.data = classo_data(X, y, C)

        # define the class formulation of the problem inside the class classo_problem
        class classo_formulation:
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

        self.formulation = classo_formulation()

        # define the class model_selection inside the class classo_problem
        class model_selection:
            def __init__(self):

                # Model selection parameters
                ''' PATH PARAMETERS'''
                self.PATH = False

                class PATHparameters:
                    def __init__(self):
                        self.formulation = 'not specified'
                        self.numerical_method = 'choose'
                        # can be : '2prox' ; 'ODE' ; 'Noproj' ; 'FB' ; and any other will make the algorithm decide

                        self.n_active = False
                        delta=2.
                        nlam = 20
                        self.lambdas = np.array([10**(-delta * float(i) / nlam) for i in range(0,nlam) ] )
                        self.plot_sigma = False

                    def __repr__(self): return ('Npath = ' + str(len(self.lambdas))
                                                + '  n_active = ' + str(self.n_active)
                                                + '  lamin = ' + str(self.lambdas[-1])
                                                + '  n_lam = ' + str(len(self.lambdas))
                                                + ';  numerical_method = ' + str(self.numerical_method))

                ''' End of the definition'''
                self.PATHparameters = PATHparameters()

                ''' CROSS VALIDATION PARAMETERS'''
                self.CV = False

                class CVparameters:
                    def __init__(self):
                        self.seed = None
                        self.formulation = 'not specified'
                        self.numerical_method = 'choose'
                        # can be : '2prox' ; 'ODE' ; 'Noproj' ; 'FB' ; and any other will make the algorithm decide

                        self.Nsubset = 5  # Number of subsets used
                        self.lambdas = np.linspace(1., 1e-3, 500)
                        self.oneSE = True

                    def __repr__(self): return ('Nsubset = ' + str(self.Nsubset)
                                                + '  lamin = ' + str(self.lambdas[-1])
                                                + '  n_lam = ' + str(len(self.lambdas))
                                                + ';  numerical_method = ' + str(self.numerical_method))

                ''' End of the definition'''
                self.CVparameters = CVparameters()

                ''' STABILITY SELECTION PARAMETERS'''
                self.StabSel = True            # Only model selection that is used by default

                class StabSelparameters:
                    def __init__(self):
                        self.seed = None
                        self.formulation = 'not specified'
                        self.numerical_method = 'choose'
                        # can be : '2prox' ; 'ODE' ; 'Noproj' ; 'FB' ; and any other will make the algorithm decide

                        self.method = 'first'  # Can be 'first' ; 'max' or 'lam'
                        self.B = 50
                        self.q = 10
                        self.percent_nS = 0.5
                        self.lamin = 1e-2  # the lambda where one stop for 'max' method
                        self.hd = False  # if set to True, then the 'max' will stop when it reaches n-k actives parameters
                        self.lam = 'theoritical'  # can also be a float, for the 'lam' method
                        self.true_lam = True
                        self.threshold = 0.8
                        self.threshold_label = 0.7
                        self.theoritical_lam = 0.0

                    def __repr__(self): return ('method = ' + str(self.method)
                                                + ';  lamin = ' + str(self.lamin)
                                                + ';  lam = ' + str(self.lam)
                                                + ';  B = ' + str(self.B)
                                                + ';  q = ' + str(self.q)
                                                + ';  percent_nS = ' + str(self.percent_nS)
                                                + ';  threshold = ' + str(self.threshold)
                                                + ';  numerical_method = ' + str(self.numerical_method))

                ''' End of the definition'''
                self.StabSelparameters = StabSelparameters()

                ''' PROBLEM AT A FIXED LAMBDA PARAMETERS'''
                self.LAMfixed = False

                class LAMfixedparameters:
                    def __init__(self):
                        self.lam = 'theoritical'
                        self.formulation = 'not specified'
                        self.numerical_method = 'choose'
                        self.true_lam = True
                        self.theoritical_lam = 0.0
                        # can be : '2prox' ; 'ODE' ; 'Noproj' ; 'FB' ; and any other will make the algorithm decide

                    def __repr__(self): return ('lam = ' + str(self.lam)
                                                + ';  theoritical_lam = ' + str(round(self.theoritical_lam, 4))
                                                + ';  numerical_method = ' + str(self.numerical_method))

                ''' End of the definition'''
                self.LAMfixedparameters = LAMfixedparameters()

            def __repr__(self):
                string = ''
                if self.PATH: string += 'Path,  '
                if self.CV: string += 'Cross Validation,  '
                if self.StabSel: string += 'Stability selection, '
                if self.LAMfixed: string += 'Lambda fixed'
                return string

        self.model_selection = model_selection()


    # This method is the way to solve the model selections contained in the object model_selection, with the formulation of 'formulation' and the data.
    def solve(self):

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
            param.theoritical_lam = theoritical_lam(int(n * param.percent_nS), d)
            if(param.true_lam): param.theoritical_lam = param.theoritical_lam*int(n * param.percent_nS)

            solution.StabSel = solution_StabSel(matrices, param, self.formulation)

        # Compute the c-lasso problem at a fixed lam thanks to the class solution_LAMfixed which contains directely the computation in the initialisation
        if self.model_selection.LAMfixed:
            param = self.model_selection.LAMfixedparameters
            param.theoritical_lam = theoritical_lam(n, d)
            if(param.true_lam): param.theoritical_lam = param.theoritical_lam*n
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



'''
Here is now the class of the object 'solution' that will be filled when the method solve() will be used. 
It does not contain much for now, but it has always four attributes : PATH ; CV ; StabSel ; LAMfixed . 

It corresponds to the 4 model selections implemented here. Default parameter is that we only compute StabSel with its own default parameters

It also has a metho __repr__ which gives the final plot of the solution is the respectives plots of each model selection + the running time for each.

Each class solution_... has its own method __repr__ that plot some graphs and/or write something. 

'''
class classo_solution:
    def __init__(self):
        self.PATH = 'not computed' #this will be filled with an object of the class 'solution_PATH' when the method solve() will be used.
        self.CV = 'not computed'  # will be an object of the class 'solution_PATH'
        self.StabSel = 'not computed' # will be an object of the class 'solution_StabSel'
        self.LAMfixed = 'not computed'

    def __repr__(self):
        return ("SPEEDNESS : " + '\n'
                                 'Running time for Path computation    : ' + self.PATH.__repr__() + '\n'
                + 'Running time for Cross Validation    : ' + self.CV.__repr__() + '\n'
                + 'Running time for Stability Selection : ' + self.StabSel.__repr__() + '\n'
                + 'Running time for Fixed LAM           : ' + self.LAMfixed.__repr__()
                )


#Here, the main function used is pathlasso ; from the file compact_func
class solution_PATH:
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
        self.time = time() - t0

    def __repr__(self):
        affichage(self.BETAS, self.LAMBDAS, labels=label,
                  title=self.formulation.name() + ' Path for the method ' + self.method), plt.show()
        if(type(self.SIGMAS)!=str and self.plot_sigma):
            plt.plot(self.LAMBDAS, self.SIGMAS), plt.ylabel("sigma/sigMAX"), plt.xlabel("lambda")
            plt.title('Sigma for Concomitant'), plt.savefig('Sigma for Concomitant' + '.png'), plt.show()
        return (str(round(self.time, 3)) + "s")

#Here, the main function used is CV ; from the file cross_validation
class solution_CV:
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

    def __repr__(self):
        plt.bar(range(len(self.refit)), self.refit), plt.title("Cross Validation refit"), plt.show()
        return (str(round(self.time, 3)) + "s")

    def graphic(self, mse_max=1.):
        i_min, i_1SE = self.index_min, self.index_1SE
        for j in range(len(self.xGraph)):
            if (self.yGraph[j] < mse_max): break

        plt.errorbar(self.xGraph[j:], self.yGraph[j:], self.standard_error[j:], label='mean over the k groups of data')
        plt.plot(self.xGraph[i_min], self.yGraph[i_min], 'k+', label='lam that minimize MSE')
        plt.plot(self.xGraph[i_1SE], self.yGraph[i_1SE], 'r+', label='lam with 1SE')
        plt.ylabel('mean of residual over lambda'), plt.xlabel('lam')
        plt.legend(), plt.title("Selection of lambda with Cross Validation"), plt.show()

#Here, the main function used is stability ; from the file stability selection
class solution_StabSel:
    def __init__(self, matrices, param, formulation):
        t0 = time()

        # Formulation choosing
        if param.formulation == 'not specified': param.formulation = formulation
        name_formulation = param.formulation.name()

        rho = param.formulation.rho
        rho_classification = param.formulation.rho_classification
        e = param.formulation.e
        # Compute the theoritical lam if necessary
        if param.lam == 'theoritical':
            lam = param.theoritical_lam
        else:
            lam = param.lam

        # Algorithmic method choosing
        numerical_method = choose_numerical_method(param.numerical_method, 'SS', param.formulation,
                                                   SSmethod=param.method, lam=lam)
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

        self.refit = min_LS(matrices, self.selected_param)
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
        plt.bar(range(len(Dselected)), Dselected, color='r', label='selected parameters')
        plt.bar(range(len(Dunselected)), Dunselected, color='b', label='unselected parameters')
        if (type(label) != bool): plt.xticks(self.to_label, label[self.to_label], rotation=30)
        plt.legend(), plt.title("Distribution of Stability Selection"), plt.show()
        print("SELECTED PARAMETERS : ")
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
                    plt.plot(lambdas, [Dpath[j][i] for j in range(N)], 'r', label='selected parameters')
                else:
                    plt.plot(lambdas, [Dpath[j][i] for j in range(N)], 'b', label='unselected parameters')
            p1, p2 = mpatches.Patch(color='red', label='selected parameters'), mpatches.Patch(color='blue',
                                                                                              label='unselected parameters')
            plt.legend(handles=[p1, p2])
            plt.title("Distribution of probability of apparence as a function of lambda"), plt.show()

        plt.bar(range(len(self.refit)), self.refit), plt.title(
            "Solution for Stability Selection with refit"), plt.show()
        return (str(round(self.time, 3)) + "s")

#Here, the main function used is Classo ; from the file compact_func
class solution_LAMfixed:
    def __init__(self, matrices, param, formulation):
        t0 = time()
        self.formulation = formulation
        # Formulation choosing
        if param.formulation == 'not specified': param.formulation = formulation
        name_formulation = param.formulation.name()

        rho = param.formulation.rho
        rho_classification = param.formulation.rho_classification
        e = param.formulation.e
        # Compute the theoritical lam if necessary
        if param.lam == 'theoritical':
            lam = param.theoritical_lam
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

    def __repr__(self):
        plt.bar(range(len(self.refit)), self.refit), plt.title("Solution for a fixed lambda with refit"), plt.show()
        if(self.formulation.concomitant) : print("SIGMA FOR LAMFIXED  : ", self.sigma )
        return (str(round(self.time, 3)) + "s")


''' Annex function in order to choose the right numerical method, if the one gave is invalid'''


def choose_numerical_method(method, model, formulation, SSmethod=None, lam=None):
    if (formulation.classification): return ('ODE')

    # cases where we use classo at a fixed lambda    
    elif (model == 'LAM') or (model == 'SS' and SSmethod == 'lam'):

        if formulation.concomitant:
            if not method in ['ODE', '2prox']:
                if (lam > 0.05):
                    return 'ODE'
                else:
                    return '2prox'

        else:
            if not method in ['ODE', '2prox', 'FB', 'Noproj']:
                if (lam > 0.1):
                    return 'ODE'
                else:
                    return '2prox'



    # cases where we use pathlasso
    else:
        if formulation.classification:
            if not method in ['ODE', '2prox', 'FB']: return 'ODE'

        elif formulation.concomitant:
            if not method in ['ODE', '2prox']: return 'ODE'

        else:
            if not method in ['ODE', '2prox', 'FB', 'Noproj']: return 'ODE'

    return method

# Author: Shelby Falde
# Course: CS131
# NOTE: I modeled a lot of the code off the given pseudocode, so there may be big sections without comments out of nowhere. Where that happens, I will put above: "#PSEUDO-CONVERT" to clarify.

from brewparse import parse_program
from intbase import *

class Interpreter(InterpreterBase):
    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)   # call InterpreterBase's constructor

    def run(self, program):

        ast = parse_program(program) # returns list of function nodes
        self.variable_name_to_value = {} # dict to hold vars
        main_func_node = self.get_main_func_node(ast)
        #self.output(main_func_node)
        self.run_func(main_func_node)

    # returns 'main' func node from the dict input.
    def get_main_func_node(self, ast):

        # returns functions sub-dict, 'functions' is a value
        func_list = ast.dict['functions'] 

        # checks for function whose name is 'main'
        for func in func_list:
            if func.dict['name'] == "main":
                return func
        
        # define error for 'main' not found.
        super().error(ErrorType.NAME_ERROR, "No main() function was found")


    # self explanatory
    def run_func(self, func_node):
        # statements key for sub-dict.
        for statement_node in func_node.dict['statements']:
            # self.output(statement_node)
            self.run_statement(statement_node)
    
    #PSEUDO-CONVERT
    def run_statement(self, statement_node):
        if self.is_definition(statement_node):
            self.do_definition(statement_node)
        elif self.is_assignment(statement_node):
            self.do_assignment(statement_node)
        elif self.is_func_call(statement_node):
            self.do_func_call(statement_node)
    
    #PSEUDO-CONVERT
    def is_definition(self, statement_node):
        return (True if statement_node.elem_type == "vardef" else False)
    def is_assignment(self, statement_node):
        return (True if statement_node.elem_type == "=" else False)
    def is_func_call(self, statement_node):
        return (True if statement_node.elem_type == "fcall" else False)


    def do_definition(self, statement_node):
        # just add to var_name_to_value dict

        target_var_name = self.get_target_variable_name(statement_node)
        if target_var_name in self.variable_name_to_value:
            super().error(ErrorType.NAME_ERROR, f"Variable {target_var_name} defined more than once",)
        else:
            self.variable_name_to_value[target_var_name] = None
        
    #PSEUDO-CONVERT
    def do_assignment(self, statement_node):
        target_var_name = self.get_target_variable_name(statement_node)
        if not self.var_name_exists(target_var_name):
            # error called for not declared var, and states it
            super().error(ErrorType.NAME_ERROR, f"Variable used and not defined: {target_var_name}", )
        source_node = self.get_expression_node(statement_node)
        resulting_value = self.evaluate_expression(source_node)
        self.variable_name_to_value[target_var_name] = resulting_value
        # below actually quite important during testing
        # self.output(self.variable_name_to_value[target_var_name])

    def do_func_call(self, statement_node):
        func_call = statement_node.dict['name']
        if func_call == "print":
            output = ""
            # loop through each arg in args list for print, evaluate their expressions, concat, and output.
            for arg in statement_node.dict['args']:
                # note, cant concat unles its str type
                output += str(self.evaluate_expression(arg))
            # THIS IS 1/2 OF ONLY REAL SELF.OUTPUT
            self.output(output)
        elif func_call == "inputi":

            # too many inputi params
            if len(statement_node.dict['args']) > 1:
                super().error(ErrorType.NAME_ERROR,f"No inputi() function found that takes > 1 parameter",)
            elif len(statement_node.dict['args']) == 1:
                arg = statement_node.dict['args'][0]
                # THIS IS 2/2 OF ONLY REAL SELF.OUTPUT
                self.output(self.evaluate_expression(arg))
                #output = str(self.evaluate_expression(arg))

            # if no args, dont output anything.


            # everything below is fine.
            user_in = super().get_input()
            try:
                user_in = int(user_in)
                return user_in
            except:
                return user_in
        
        # Catch unknown function calls
        else:
            super().error(ErrorType.NAME_ERROR, f"Function {func_call} is not defined", )
        

    #PSEUDO-CONVERT
    def get_target_variable_name(self, statement_node):
        return statement_node.dict['name']
    def var_name_exists(self, varname):
        return True if varname in self.variable_name_to_value.keys() else False
    def get_expression_node(self, statement_node):
        return statement_node.dict['expression']
    
    #PSEUDO-CONVERT
    def is_value_node(self, expression_node):
        return True if (expression_node.elem_type in ["int", "string"]) else False
    def is_variable_node(self, expression_node):
        return True if (expression_node.elem_type == "var") else False
    def is_binary_operator(self, expression_node):
        return True if (expression_node.elem_type in ["+", "-"]) else False

    #PSEUDO-CONVERT
    def evaluate_expression(self, expression_node):
        # self.output(expression_node)
        if self.is_value_node(expression_node):
            return self.get_value(expression_node)
        elif self.is_variable_node(expression_node):
            return self.get_value_of_variable(expression_node)
        elif self.is_binary_operator(expression_node):
            return self.evaluate_binary_operator(expression_node)
        elif self.is_func_call(expression_node):
            return self.do_func_call(expression_node)

    def get_value(self, expression_node):
        # Returns value assigned to key 'val'
        return expression_node.dict['val']
    def get_value_of_variable(self, expression_node):
        # returns value under the variable name provided.
        # NEED TO CATCH: if var NOT ASSIGNED VALUE YET: ex: {var x; print(x);}
        # NOTE this is how its done in barista, feels bad if we were to add concatonation in future, or something else. NOT FUTURE PROOF.
        target_var_name = expression_node.dict['name']
        if not self.var_name_exists(target_var_name):
            # error called for not declared var, and states it
            super().error(ErrorType.NAME_ERROR, f"Variable used and not defined: {target_var_name}", )
        val = self.variable_name_to_value[target_var_name]
        if val is None:
            return 0
        else:
            return val


    # + or -
    def evaluate_binary_operator(self, expression_node):
        # can *only* be + or -.. for now.
        # returns arg1 - arg2 (allows for nested/recursive calls should something like 5+8-6 happen)
        # self.output(expression_node)

        # check if valid args (same int type)
        op1 = self.evaluate_expression(expression_node.dict['op1'])
        op2 = self.evaluate_expression(expression_node.dict['op2'])

        if (type(op1) is not type(op2)) or (type(op1) == str) or (type(op2) == str):
            # type checking
            self.output(f"op1: {type(op1)}  op2: {type(op2)}")
            super().error(ErrorType.TYPE_ERROR, f"Incompatible types for {expression_node.elem_type} operation",)

        if expression_node.elem_type == "+":
            return (op1 + op2)
        elif expression_node.elem_type == "-":
            # self.output(expression_node)
            return (op1 - op2)


    # No more functions remain... for now... :)

# FOR DEBUGGING
program = """
            func main() {
      
             var v;
             var v;
             
            }"""
# z should be '1'
interpreter = Interpreter()
interpreter.run(program)
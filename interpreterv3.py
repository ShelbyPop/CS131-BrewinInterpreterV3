# Author: Shelby Falde
# Course: CS131

from brewparse import *
from intbase import *

nil = Element("nil")

class Interpreter(InterpreterBase):
    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)  
        self.func_defs = [] # Global Function Def
        self.struct_defs = [] # Global Struct Def
        self.variable_scope_stack = [{}] # Stack to hold variable scopes
        
    def run(self, program):
        ast = parse_program(program) # returns list of function nodes
        #self.output(ast) # always good for start of assignment to see new parser
        self.struct_defs = self.get_struct_defs(ast)
        self.func_defs = self.get_func_defs(ast)
        main_func_node = self.get_main_func_node(ast)
        self.run_func(main_func_node)

    # grabs all globally defined functions to call when needed.
    def get_func_defs(self, ast):
        return ast.dict['functions']

    # grabs all globally defined struct defs
    def get_struct_defs(self, ast):
        #for item in ast.dict['structs']:
            #self.output(item)
        return ast.dict['structs']

    # returns 'main' func node from the dict input.
    def get_main_func_node(self, ast):
        for func in self.func_defs:
            if func.dict['name'] == "main":
                return func
        super().error(ErrorType.NAME_ERROR, "No main() function was found",)

    def run_func(self, func_node):
        ### BEGIN FUNC SCOPE ###
        self.variable_scope_stack.append({})
        return_value = nil
        for statement in func_node.dict['statements']:
            return_value = self.run_statement(statement)
            # check if statement results in a return, and return a return statement with 
            if isinstance(return_value, Element) and return_value.elem_type == "return":
                # Return the value, dont need to continue returning.
                ## check type validity ##
                self.variable_scope_stack.pop()
                ret_value = self.check_coercion(eval(func_node.dict['return_type']), return_value) # type coercion bool->int
                self.check_same_type(eval(func_node.dict['return_type']), type(return_value.get("value")), "func_ret")
                # self.output(func_node.dict['return_type'])
                return ret_value
            if return_value is not nil:
                ## check type validity ##
                #eval() converts string to python type class (actually cool)
                return_value = self.check_coercion(eval(func_node.dict['return_type']), return_value) # type coercion bool->int
                #self.output(return_value)
                self.check_same_type(eval(func_node.dict['return_type']), type(return_value), "func_ret")
                break
        
        ### END FUNC SCOPE ###
        self.variable_scope_stack.pop()
        return return_value
    
    def run_statement(self, statement_node):
        #print(f"Running statement: {statement_node}")
        if self.is_definition(statement_node):
            self.do_definition(statement_node)
        elif self.is_assignment(statement_node):
            self.do_assignment(statement_node)
        elif self.is_func_call(statement_node):
            return self.do_func_call(statement_node)
        elif self.is_return_statement(statement_node):
            return self.do_return_statement(statement_node)
        elif self.is_if_statement(statement_node):
            return self.do_if_statement(statement_node)
        elif self.is_for_loop(statement_node):
            return self.do_for_loop(statement_node)
        return nil
    
    def is_definition(self, statement_node):
        return (True if statement_node.elem_type == "vardef" else False)
    def is_assignment(self, statement_node):
        return (True if statement_node.elem_type == "=" else False)
    def is_func_call(self, statement_node):
        return (True if statement_node.elem_type == "fcall" else False)
    def is_return_statement(self, statement_node):
        return (True if statement_node.elem_type == "return" else False)
    def is_if_statement(self, statement_node):
        return (True if statement_node.elem_type == "if" else False)
    def is_for_loop(self, statement_node):
        return (True if statement_node.elem_type == "for" else False)

    def do_definition(self, statement_node):
        # just add to var_name_to_value dict
        target_var_name = self.get_target_variable_name(statement_node)
        #self.output(statement_node)
        if target_var_name in self.variable_scope_stack[-1]:
            super().error(ErrorType.NAME_ERROR, f"Variable {target_var_name} defined more than once",)
        else:
            
            self.assign_default_values(statement_node,target_var_name)
            # self.variable_scope_stack[-1][target_var_name] = None  ## DEPRECATED IN V3 ##
        
    # New in V3
    def assign_default_values(self, statement_node, target_var_name):
        #self.output(statement_node.dict['var_type'])
        self.output(statement_node)
        match statement_node.dict['var_type']:
            case "int":
                self.variable_scope_stack[-1][target_var_name] = 0
            case "bool":
                self.variable_scope_stack[-1][target_var_name] = False
            case "string":
                self.variable_scope_stack[-1][target_var_name] = ""
            case _:
                self.variable_scope_stack[-1][target_var_name] = nil

    def struct_assign_default_values(self, statement_node, field_vars, field):
        #self.output(statement_node.dict['var_type'])
        self.output(statement_node)
        match statement_node.dict['var_type']:
            case "int":
                field_vars[field] = 0
            case "bool":
                field_vars[field] = False
            case "string":
                field_vars[field] = ""
            case _:
                field_vars[field] = nil

    def do_assignment(self, statement_node):
        #self.output(statement_node)
        target_var_name = self.get_target_variable_name(statement_node)
        for scope in reversed(self.variable_scope_stack): 
            if target_var_name in scope: 
                # Does not evaluate until after checking if valid variable
                source_node = self.get_expression_node(statement_node)
                resulting_value = self.evaluate_expression(source_node)
                #self.output(resulting_value)
                ## check type validity ## 
                #self.output(scope[target_var_name])
                resulting_value = self.check_coercion(type(scope[target_var_name]), resulting_value) # type coercion bool->int
                self.check_same_type(type(scope[target_var_name]), type(resulting_value), "assignment")
                
                scope[target_var_name] = resulting_value 
                return
        super().error(ErrorType.NAME_ERROR, f"variable used and not declared: {target_var_name}",)

    # Check if function is defined
    def check_valid_func(self, func_call):
        for func in self.func_defs:
            if func.dict['name'] == func_call:
                return True
        return False

    # Allows function overloading by first searching for func_defs for a matching name and arg length
    def get_func_def(self, func_call, arg_len):
        for func in self.func_defs:
            if func.dict['name'] == func_call and len(func.dict['args']) == arg_len:
                return func
        # Already check if func exists before calling
        # So, must not have correct args.
        super().error(ErrorType.NAME_ERROR,
                       f"Incorrect amount of arguments given: {arg_len} ",
                       )
    
    def do_func_call(self, statement_node):
        func_call = statement_node.dict['name']
        if func_call == "print":
            output = ""
            # loop through each arg in args list for print, evaluate their expressions, concat, and output.
            for arg in statement_node.dict['args']:
                eval_ = self.evaluate_expression(arg)
                # note, cant concat unles its str type
                if type(eval_) is bool:
                    if eval_:
                        output += "true"
                    else: 
                        output += "false"
                else:
                    output += str(self.evaluate_expression(arg))
            # THIS IS 1/3 OF ONLY REAL SELF.OUTPUT
            self.output(output)
            return nil
        elif func_call == "inputi":
            ## NOTE: this may come up in the git history as 'copy and pasted' but its because 
            # my git repo didnt have this inputi() version, but my submission for project 1 did.
            # too many inputi params
            if len(statement_node.dict['args']) > 1:
                super().error(ErrorType.NAME_ERROR,f"No inputi() function found that takes > 1 parameter",)
            elif len(statement_node.dict['args']) == 1:
                arg = statement_node.dict['args'][0]
                # THIS IS 2/3 OF ONLY REAL SELF.OUTPUT
                self.output(self.evaluate_expression(arg))
            user_in = super().get_input()
            try:
                user_in = int(user_in)
                return user_in
            except:
                return user_in
        
        # same as inputi but for strings
        elif func_call == "inputs":
            # too many inputi params
            if len(statement_node.dict['args']) > 1:
                super().error(ErrorType.NAME_ERROR,f"No inputs() function found that takes > 1 parameter",)
            elif len(statement_node.dict['args']) == 1:
                arg = statement_node.dict['args'][0]
                # THIS IS 3/3 OF ONLY REAL SELF.OUTPUT
                self.output(self.evaluate_expression(arg))
            user_in = super().get_input()
            try:
                user_in = int(user_in)
                return user_in
            except:
                return user_in
        else:
            ## USER-DEFINED FUNCTION ##
            if not self.check_valid_func(func_call):
                super().error(ErrorType.NAME_ERROR,
                                f"Function {func_call} was not found",
                                )
            func_def = self.get_func_def(func_call, len(statement_node.dict['args']))
            ##### Start Function Call ######

            #### START FUNC SCOPE ####
            # Assign Arguments:
            args = statement_node.dict['args'] # passed in arguments
            params = func_def.dict['args'] # function parameters
            processed_args = [{}]
            for i in range(0,len(params)):
                var_name = params[i].dict['name']
                var_type = params[i].dict['var_type']
                arg_value = self.evaluate_expression(args[i])
                ## check type validity ##
                # self.output(eval(var_type))
                arg_value = self.check_coercion(eval(var_type), arg_value) # type coercion bool->int
                self.check_same_type(eval(var_type), type(arg_value), "parameter")
                processed_args[-1][var_name] = arg_value
            main_vars = self.variable_scope_stack.copy()

            # Scope is only Args
            self.variable_scope_stack = processed_args
            return_value = self.run_func(func_def) # Actual function run
            
            #### END FUNC SCOPE ####
            self.variable_scope_stack = main_vars.copy()

            return return_value          
            ##### End Function Call ######
    
    def do_return_statement(self, statement_node):
        if not statement_node.dict['expression']:
            #return 'nil' Element
            return Element("return", value=nil)
        return self.evaluate_expression(statement_node.dict['expression'])

    # Scope rules: Can access parent calling vars, but vars they create are deleted after scope.
    # So, keep track of what vars were before, and after end of clause, wipe those variables.
    def do_if_statement(self, statement_node):
        condition = statement_node.dict['condition']
        condition = self.evaluate_expression(condition)
        # error if condition is non-boolean
        if type(condition) is not bool:
            super().error(ErrorType.TYPE_ERROR, "Condition is not of type bool",)
        statements = statement_node.dict['statements']
        else_statements = statement_node.dict['else_statements']

        ### BEGIN IF SCOPE ###
        self.variable_scope_stack.append({})
        if condition:
            for statement in statements:
                return_value = self.run_statement(statement)     
                if isinstance(return_value, Element) and return_value.elem_type == "return":
                    #end scope early and return
                    self.variable_scope_stack.pop()
                    return Element("return", value=return_value.get("value"))
                elif return_value is not nil:
                    self.variable_scope_stack.pop()
                    return Element("return", value=return_value)
                    # if return needed, stop running statements, immediately return the value.
        else:
            if else_statements:
                for else_statement in else_statements:
                    return_value = self.run_statement(else_statement)
                    
                    if isinstance(return_value, Element) and return_value.elem_type == "return":
                        #end scope early and return
                        self.variable_scope_stack.pop()
                        return Element("return", value=return_value.get("value"))
                    elif return_value is not nil:
                        self.variable_scope_stack.pop()
                        return Element("return", value=return_value)
        ### END IF SCOPE ###
        self.variable_scope_stack.pop()
        return nil

    def do_for_loop(self, statement_node):
        # Run initializer
        init_node = statement_node.dict['init']
        self.run_statement(init_node)
        update = statement_node.dict['update']
        condition = statement_node.dict['condition']
        statements = statement_node.dict['statements']
        
        # Run the loop again (exits on condition false)
        while self.evaluate_expression(condition):
            if type(self.evaluate_expression(condition)) is not bool:
                super().error(ErrorType.TYPE_ERROR, "Condition is not of type bool",)
            
            ### BEGIN VAR SCOPE ###
            self.variable_scope_stack.append({})

            for statement in statements:
                return_value = self.run_statement(statement)
                # if return keyword
                if isinstance(return_value, Element) and return_value.elem_type == "return":

                    #end scope early and return
                    self.variable_scope_stack.pop()
                    return Element("return", value=return_value.get("value"))
                elif return_value is not nil:
                    return Element("return", value=return_value)

            ### END VAR SCOPE ###
            self.variable_scope_stack.pop()

            self.run_statement(update)
        return nil
        
    # helper functions
    def get_target_variable_name(self, statement_node):
        return statement_node.dict['name']
    def get_expression_node(self, statement_node):
        return statement_node.dict['expression']
    
    # basically pseudocode, self-explanatory
    def is_value_node(self, expression_node):
        return True if (expression_node.elem_type in ["int", "string", "bool", "nil"]) else False
    def is_variable_node(self, expression_node):
        return True if (expression_node.elem_type == "var") else False
    def is_binary_operator(self, expression_node):
        return True if (expression_node.elem_type in ["+", "-", "*", "/"]) else False
    def is_unary_operator(self, expression_node):
        return True if (expression_node.elem_type in ["neg", "!"]) else False
    def is_comparison_operator(self, expression_node):
        return True if (expression_node.elem_type in ['==', '<', '<=', '>', '>=', '!=']) else False
    def is_binary_boolean_operator(self, expression_node):
        return True if (expression_node.elem_type in ['&&', '||']) else False
    def is_struct_def(self, expression_node):
        return True if (expression_node.elem_type == "new") else False

    # basically pseudcode, self-explanatory
    def evaluate_expression(self, expression_node):
        #self.output(expression_node)
        if self.is_value_node(expression_node):
            return self.get_value(expression_node)
        elif self.is_variable_node(expression_node):
            return self.get_value_of_variable(expression_node)
        elif self.is_binary_operator(expression_node):
            return self.evaluate_binary_operator(expression_node)
        elif self.is_unary_operator(expression_node):
            return self.evaluate_unary_operator(expression_node)
        elif self.is_comparison_operator(expression_node):
            return self.evaluate_comparison_operator(expression_node)
        elif self.is_binary_boolean_operator(expression_node):
            return self.evaluate_binary_boolean_operator(expression_node)
        elif self.is_func_call(expression_node):
            return self.do_func_call(expression_node)
        elif self.is_struct_def(expression_node):
            return self.do_struct_def(expression_node)

    def get_value(self, expression_node):
        # Returns value assigned to key 'val'
        if expression_node.elem_type == "nil":
            return nil
        return expression_node.dict['val']

    # returns value under the variable name provided.
    def get_value_of_variable(self, expression_node): 
        if expression_node == 'nil':
            return nil
        var_name = expression_node.dict['name']
        for scope in reversed(self.variable_scope_stack): 
            if var_name in scope: 
                val = scope[var_name] 
                # Error deprecated in V3
                # if val is None:
                #     super().error(ErrorType.NAME_ERROR, f"variable '{var_name}' declared but not defined",)
                # else: 
                return val 
        # if varname not found
        super().error(ErrorType.NAME_ERROR, f"variable '{var_name}' used and not declared",)

    def do_struct_def(self,expression_node):
        struct_name = expression_node.dict['var_type']
        # find the struct def
        for _def in self.struct_defs:
            struct_def = _def if (_def.dict['name'] == struct_name) else nil
            if (struct_def is not nil):
                break
        # if we never found a struct_def
        if struct_def is nil:
            super().error(ErrorType.TYPE_ERROR, f"struct '{struct_name}' used but not defined",) ##TODO: FIX ERROR TYPE?
        
        return self.evaluate_struct_def(struct_def) # do struct assignment

    # Evalautes a struct def by returning a dict of variables.
    def evaluate_struct_def(self,struct_def):
        field_vars = {}

        for fielddef in struct_def.dict['fields']:
            self.struct_assign_default_values(fielddef, field_vars, fielddef.dict['name'])
        
        return field_vars

    # + or -
    def evaluate_binary_operator(self, expression_node):
        # can *only* be +, -, *, / for now.
        eval1 = self.evaluate_expression(expression_node.dict['op1'])
        eval2 = self.evaluate_expression(expression_node.dict['op2'])
        # for all operators other than + (for concat), both must be of type 'int'
        if (expression_node.elem_type != "+") and not (type(eval1) == int and type(eval2) == int):
            super().error(ErrorType.TYPE_ERROR, "Arguments must be of type 'int'.",)
        if (expression_node.elem_type == "+") and not ((type(eval1) == int and type(eval2) == int) or (type(eval1) == str and type(eval2) == str)):
            super().error(ErrorType.TYPE_ERROR, "Types for + must be both of type int or string.",)
        if expression_node.elem_type == "+":
            return (eval1 + eval2)
        elif expression_node.elem_type == "-":
            return (eval1 - eval2)
        elif expression_node.elem_type == "*":
            return (eval1 * eval2)
        elif expression_node.elem_type == "/":
            # integer division
            return (eval1 // eval2)


    def evaluate_unary_operator(self, expression_node):
        # can be 'neg' (-b) or  '!' for boolean
        eval = self.evaluate_expression(expression_node.dict['op1'])
        if expression_node.elem_type == "neg":
            if not (type(eval) == int):
                super().error(ErrorType.TYPE_ERROR, "'negation' can only be used on integer values.",)
            return -(eval)
        if expression_node.elem_type == "!":
            if not (type(eval) == bool):
                super().error(ErrorType.TYPE_ERROR, "'Not' can only be used on boolean values.",)
            return not (eval)
        
    # there's probably a better way to do this but oh well
    def evaluate_comparison_operator(self, expression_node):
        eval1 = self.evaluate_expression(expression_node.dict['op1'])
        eval2 = self.evaluate_expression(expression_node.dict['op2'])
        # != and == can compare different types.
        #self.output(f"eval1: {eval1} eval2: {eval2}")
        if (expression_node.elem_type not in ["!=", "=="]) and not (type(eval1) == int and type(eval2) == int):
            super().error(ErrorType.TYPE_ERROR, f"Comparison args for {expression_node.elem_type} must be of same type int.",)
        match expression_node.elem_type:
            case '<':
                return (eval1 < eval2)
            case '<=':
                return (eval1 <= eval2)
            case '==':
                if not (type(eval1) == type(eval2)):
                    return False
                else:
                    return (eval1 == eval2)
            case '>=':
                return (eval1 >= eval2)
            case '>':
                return (eval1 > eval2)
            case '!=': 
                if not (type(eval1) == type(eval2)):
                    return True
                else:
                    return (eval1 != eval2)
    
    def evaluate_binary_boolean_operator(self, expression_node):
        eval1 = self.evaluate_expression(expression_node.dict['op1'])
        eval2 = self.evaluate_expression(expression_node.dict['op2'])
        if (type(eval1) is not bool) or (type(eval2) is not bool):
            super().error(ErrorType.TYPE_ERROR, f"Comparison args for {expression_node.elem_type} must be of same type bool.",)
        # forces evaluation on both (strict evaluation)
        eval1 = bool(eval1)
        eval2 = bool(eval2)
        match expression_node.elem_type:
            case '&&':
                return (eval1 and eval2)
            case '||':
                return (eval1 or eval2)
            
    ## Type Checking Functions ##
    # coerce int to bool (if arg1 is type bool)
    def check_coercion(self, arg1, arg2):
        if (arg1 is bool) and isinstance(arg2, int):
            return bool(arg2)
        else:
            return arg2

    # type1 - var type, param type, func return type
    # type2 - value/expression type
    def check_same_type(self, type1, type2, area):
        # Error for type checking: "in assignment", "on formal parameter {var_name}", "inconsistent with function return type {int}"
        ### No type coercion from int->bool for now ###
        if area == "assignment":
            if type1 != type2:

                super().error(ErrorType.TYPE_ERROR, f"Type mismatch {type1.__name__} vs {type2.__name__} in assignment",)
            else:
                return
        if area == "parameter":
            if type1 != type2:
                super().error(ErrorType.TYPE_ERROR, f"Type mismatch on formal parameter with type: {type1.__name__}",)
            else:
                return
        if area == "func_ret":
            if type1 != type2:
                super().error(ErrorType.TYPE_ERROR, f"Function return type {type1.__name__} is inconsistent with function's return type {type2.__name__}",)
            else:
                return

    # No more functions remain... for now... :)

#DEBUGGING
program = """
struct Person {
  name: string;
  age: int;
  student: bool;
}

struct Person2 {
  name: string;
  age: int;
  student: bool;
}

func main() : void {
  var test: bool;
  test = false;
  var p: Person;
  p = new Person;

  print("hi!");
}
"""
interpreter = Interpreter()
interpreter.run(program)

# Author: Shelby Falde
# Course: CS131

from brewparse import *
from intbase import *

nil = Element("nil")

class Interpreter(InterpreterBase):
    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)   # call InterpreterBase's constructor
        # Since functions (at the top level) can be created anywhere, we'll just do a search for function definitions and assign them 'globally'
        self.func_defs = []
        self.struct_defs = {} # Global Struct Def
        self.variable_scope_stack = [{}] # Stack to hold variable scopes
        
    def run(self, program):
        ast = parse_program(program) # returns list of function nodes
        #self.output(ast) # always good for start of assignment
        self.struct_defs = self.get_struct_defs(ast)
        self.func_defs = self.get_func_defs(ast)
        main_func_node = self.get_main_func_node(ast)
        self.run_func(main_func_node)

    # grabs all globally defined struct defs
    def get_struct_defs(self, ast):
        #for item in ast.dict['structs']:
            #self.output(item)
        return ast.dict['structs']

    # grabs all globally defined functions to call when needed.
    def get_func_defs(self, ast):
        # returns functions sub-dict, 'functions' is key
        return ast.dict['functions']

    # returns 'main' func node from the dict input.
    def get_main_func_node(self, ast):
        # checks for function whose name is 'main'
        for func in self.func_defs:
            if func.dict['name'] == "main":
                return func
        # define error for 'main' not found.
        super().error(ErrorType.NAME_ERROR, "No main() function was found",)

    # self explanatory
    def run_func(self, func_node):
        # statements key for sub-dict.
        ### BEGIN FUNC SCOPE ###
        self.variable_scope_stack.append({})
        return_value = nil
        func_ret_type = func_node.dict['return_type']

        for statement in func_node.dict['statements']:
            return_value = self.run_statement(statement)
            # check if statement results in a return, and return a return statement with 
            if isinstance(return_value, Element) and return_value.elem_type == "return":
                # Return the value, dont need to continue returning.
                self.variable_scope_stack.pop()
                return_value = return_value.get("value")
                # Perform type checking
                if return_value is nil:
                    return_value = self.get_default_value(func_ret_type)
                    self.output(f"return value is: {return_value}, function return type is: {func_ret_type}")

                if func_ret_type == "bool":
                    return_value = self.check_coercion(return_value)
                if not self.check_valid_type(return_value, func_ret_type):
                    #self.output(return_value)
                    super().error(ErrorType.TYPE_ERROR, f"Return type misaligns with functions return type: {func_ret_type}",)
                return return_value
            if return_value is not nil:
                break
        
        ### END FUNC SCOPE ###
        self.variable_scope_stack.pop()
        if return_value is nil:
            return self.get_default_value(func_ret_type)
        return return_value
    
    # Let's define the default values here, and just assign in the definition.
    # Switching to if else to do 'type_name in self.struct_defs'
    def get_default_value(self, type_name):
        if type_name == "int":
            return 0
        elif type_name == "bool":
            return False
        elif type_name == "string":
            return ""
        elif type_name in self.struct_defs:
            return nil
        elif type_name == "void":
            return nil
        else:
            super().error(ErrorType.TYPE_ERROR, f"Unknown type: {type_name}")

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
        target_var_type = self.get_target_variable_type(statement_node)
        if target_var_name in self.variable_scope_stack[-1]:
            super().error(ErrorType.NAME_ERROR, f"Variable {target_var_name} defined more than once",)
        else:
            # I liked variables being a dict with 'value' and 'type', let's do that again
            self.variable_scope_stack[-1][target_var_name] = {
                'value' : self.get_default_value(target_var_type),
                'type' : target_var_type
            }
        
    def do_assignment(self, statement_node):
        target_var_name = self.get_target_variable_name(statement_node)
        source_node = self.get_expression_node(statement_node)
        resulting_value = self.evaluate_expression(source_node)

        for scope in reversed(self.variable_scope_stack): 
            if target_var_name in scope: 
                # Does not evaluate until after checking if valid variable
                var_type = scope[target_var_name]['type']
                ## Perform Type Checking ##
                if self.check_valid_type(resulting_value, var_type):
                    # only set value if valid (allows int->bool)
                    scope[target_var_name]['value'] = resulting_value
                    return
                else:
                    super().error(ErrorType.NAME_ERROR, f"Invalid type {var_type} assigned to {target_var_name}",)
        super().error(ErrorType.NAME_ERROR, f"variable used and not declared: {target_var_name}",)


    # Checks if function is defined
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
                eval = self.evaluate_expression(arg)
                # note, cant concat unles its str type
                if type(eval) is bool:
                    if eval:
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
            # Check if function is defined
            if not self.check_valid_func(func_call):
                super().error(ErrorType.NAME_ERROR,
                                f"Function {func_call} was not found",
                                )
            func_def = self.get_func_def(func_call, len(statement_node.dict['args']))
            ##### Start Function Call ######

            #### START FUNC SCOPE ####
            # Assign parameters to the local variable dict
            args = statement_node.dict['args'] # passed in arguments
            params = func_def.dict['args'] # function parameters
            processed_args = [{}]
            # intialize params, and then assign to them each arg in order
            for i in range(0,len(params)):
                # define params
                var_name = params[i].dict['name']
                var_type = params[i].dict['var_type']
                arg_value = self.evaluate_expression(args[i])
                #self.output(args[i])
                arg_value = self.check_coercion(arg_value) if var_type == "bool" else arg_value
                # Perform Type Checking..
                if self.check_valid_type(arg_value, var_type):
                    processed_args[-1][var_name] = {
                        'value' : arg_value,
                        'type' : var_type
                    }
                else:
                    super().error(ErrorType.TYPE_ERROR, f"Invalid arg type given to formal parameter {var_name}",)

            main_vars = self.variable_scope_stack.copy()

            # wipe all prev vars except arguments
            self.variable_scope_stack = processed_args
            return_value = self.run_func(func_def)
            
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
        if type(condition).__name__ == "int":
            condition = self.check_coercion(condition)
        # error if condition is non-boolean
        if type(condition).__name__ != "bool":
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
            if type(condition).__name__ == "int":
                condition = self.check_coercion(condition)
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
    def get_target_variable_type(self, statement_node):
        return statement_node.dict['var_type']
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
                return scope[var_name]['value']
        # if varname not found
        super().error(ErrorType.NAME_ERROR, f"variable '{var_name}' used and not declared",)


    # + or -
    def evaluate_binary_operator(self, expression_node):
        # can *only* be +, -, *, / for now.
        eval1 = self.evaluate_expression(expression_node.dict['op1'])
        eval2 = self.evaluate_expression(expression_node.dict['op2'])
        # for all operators other than + (for concat), both must be of type 'int'
        if (expression_node.elem_type != "+") and not (type(eval1) == int and type(eval2) == int):
            super().error(ErrorType.TYPE_ERROR, "Arguments must be of type 'int'.",)
        if (expression_node.elem_type == "+") and not ((type(eval1) == int and type(eval2) == int) or (type(eval1) == str and type(eval2) == str)):
            #self.output(f"eval1: {eval1} eval2: {eval2}")
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
            if type(eval).__name__ == "int":
                eval = self.check_coercion(eval)
            if not (type(eval).__name__ == "bool"):
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
        eval1 = self.check_coercion(eval1) if type(eval2).__name__ == "bool" else eval1
        eval2 = self.check_coercion(eval2) if type(eval1).__name__ == "bool" else eval2
        
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
            
    def do_struct_def(self, expression_node):
        struct_name = expression_node.dict['var_type']
        # Check if struct even exists first
        if struct_name not in self.struct_defs:
            super().error(ErrorType.TYPE_ERROR, f"struct '{struct_name}' used but not defined",)
        
        struct_def = self.struct_defs[struct_name]
        struct_fields = {}
        for fielddef in struct_def.dict['fields']:
            field_name = fielddef.dict['name']
            field_type = fielddef.dict['var_type']
            struct_fields[field_name] = {
                'value' : self.get_default_value(field_type),
                'type' : field_type                
            }
        return struct_fields

    ## Type Checking Functions ##
    # Check if a value holds the correct type for what's needed
    def check_valid_type(self, val, needs_type):
        if needs_type == "int":
            return type(val).__name__ == "int"
        elif needs_type == "bool":
            # Either int or bool is fine (coercion)
            return (type(val).__name__ == "bool") or (type(val).__name__ == "int")
        elif needs_type == "string":
            return type(val).__name__ == "string"
        elif needs_type in self.struct_defs:
            # Either the val is nil, or it's a dict of field_vars
            return (val is nil) or (type(val) is dict)
        return False
    
    def check_coercion(self, val):
        if type(val).__name__ == "int":
            return bool(val)
        else:
            return val

    # No more functions remain... for now... :)

#DEBUGGING
program = """
func main() : void {
  print(5 || false);
  var a:int;
  a = 1;
  if (a) {
    print("if works on integers now!");
  }
  foo(a-1);
}

func foo(b : bool) : void {
  print(b);
}
"""
interpreter = Interpreter()
interpreter.run(program)
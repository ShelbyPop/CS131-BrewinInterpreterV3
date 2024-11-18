- Added default values to vars
- Added type checking and type coercion (bool->int)
- Added structs + default field values
- Added struct field usability (but not assignment)
- Added field var assignment
- Fixed Struct type mismatch mistakenly showing an error in parameter passing.
- Added default return values if one returns nil

### REVERTED TO V2 ###

- Added basic type checking
- Added basic struct functionality
- Added default return values
- Added type coercion
- added basic struct field functionality (read and write)
- Need to add type checking to include struct_names
- Added Strict Struct typing (removed duck typing)
    - Removed pass by obj ref structs (need to add back)
    - or.... not? Needs more extensive testing. (I think I accidentally have it somehow)
- Fixed for loop not evaluating coercion correctly
- Added FAULT_ERROR in correct locations.
- Added error checking for evaluating a void return function in expression (hopefully didnt break anything else)
- Probably fully fixed fault vs name vs type error in field access (75/80 on gradescope!! yippeee)
- Removed ability to compare to nil (unless one of the args is a struct with no fields (i.e. variable value is nil))
- Added Type coercion to comparison (== and != only)
    - Added type checking to == (maybe not needed?) Without, 77/80, with: 70/80 (fail test_challenge 1-4, struct3, struct_cmp1&2)
- Fixed Coercion for && || operators (before only did 1 arg if other was bool, now does both no matter what)
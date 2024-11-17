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
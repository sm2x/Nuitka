#
#     Copyright 2011, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     If you submit Kay Hayen patches to this software in either form, you
#     automatically grant him a copyright assignment to the code, or in the
#     alternative a BSD license to the code, should your jurisdiction prevent
#     this. Obviously it won't affect code that comes to him indirectly or
#     code you don't submit to him.
#
#     This is to reserve my ability to re-license the code at any time, e.g.
#     the PSF. With this version of Nuitka, using it for Closed Source will
#     not be allowed.
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, version 3 of the License.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#     Please leave the whole of this copyright notice intact.
#
""" Main module code templates

"""

global_copyright = """\
// Generated code for Python source for module '%(name)s'
// created by Nuitka version %(version)s

// This code is in part copyright Kay Hayen, license GPLv3. This has the consequence that
// your must either obtain a commercial license or also publish your original source code
// under the same license unless you don't distribute this source or its binary.
"""

module_inittab_entry = """\
{ (char *)"%(module_name)s", init%(module_identifier)s },"""

main_program = """\
// Our own inittab for lookup of "frozen" modules, i.e. the ones included in this binary.
static struct _inittab _frozes_modules[] =
{
%(module_inittab)s
    { NULL, NULL }
};

// For embedded modules, to be unpacked. Used by main program only
extern void registerMetaPathBasedUnfreezer( struct _inittab *_frozes_modules );

// The main program for C++. It needs to prepare the interpreter and then calls the
// initialization code of the __main__ module.

int main( int argc, char *argv[] )
{

    Py_Initialize();
    PySys_SetArgv( argc, argv );

    // Initialize the constant values used.
    _initConstants();

    // Initialize the compiled types of Nuitka.
    PyType_Ready( &Nuitka_Generator_Type );
    PyType_Ready( &Nuitka_Function_Type );
    PyType_Ready( &Nuitka_Method_Type );
    PyType_Ready( &Nuitka_Genexpr_Type );

    enhancePythonTypes();

    // Set the sys.executable path to the original Python executable on Linux
    // or to python.exe on Windows.
    PySys_SetObject( (char *)"executable", PyString_FromString( %(sys_executable)s ) );

    // Register the initialization functions for modules included in the binary if any
    int res = PyImport_ExtendInittab( _frozes_modules );
    assert( res != -1 );

    registerMetaPathBasedUnfreezer( _frozes_modules );

    patchInspectModule();

    init__main__();

    if ( PyErr_Occurred() )
    {
        assertFrameObject( frame___main__ );
        assert( frame___main__->f_back == NULL );

        // Cleanup code may need a frame, so put it back.
        Py_INCREF( frame___main__ );
        PyThreadState_GET()->frame = frame___main__;

        PyErr_Print();
        return 1;
    }
    else
    {
        return 0;
    }
}
"""

module_header_template = """\

#include <nuitka/helpers.hpp>

NUITKA_MODULE_INIT_FUNCTION init%(module_identifier)s(void);

extern PyObject *_module_%(module_identifier)s;

class PyObjectGlobalVariable_%(module_identifier)s
{
    public:
        explicit PyObjectGlobalVariable_%(module_identifier)s( PyObject **dummy, PyObject **var_name )
        {
            assert( var_name );

            this->var_name = (PyStringObject **)var_name;
        }

        PyObject *asObject0() const
        {
            PyDictEntry *entry = GET_PYDICT_ENTRY( (PyModuleObject *)_module_%(module_identifier)s, *this->var_name );

            if (likely( entry->me_value != NULL ))
            {
                assertObject( entry->me_value );

                return entry->me_value;
            }

            entry = GET_PYDICT_ENTRY( _module_builtin, *this->var_name );

            if (likely( entry->me_value != NULL ))
            {
                assertObject( entry->me_value );

                return entry->me_value;
            }

            PyErr_Format( PyExc_NameError, "global name '%%s' is not defined", Nuitka_String_AsString( (PyObject *)*this->var_name ) );
            throw _PythonException();
        }

        PyObject *asObject() const
        {
            return INCREASE_REFCOUNT( this->asObject0() );
        }

        PyObject *asObject0( PyObject *dict ) const
        {
            PyObject *result = PyDict_GetItem( dict, (PyObject *)*this->var_name );

            if ( result != NULL )
            {
                return result;
            }
            else
            {
                return this->asObject0();
            }
        }

        void assign( PyObject *value ) const
        {
            PyDictEntry *entry = GET_PYDICT_ENTRY( (PyModuleObject *)_module_%(module_identifier)s, *this->var_name );

            // Values are more likely set than not set, in that case speculatively try the
            // quickest access method.
            if (likely( entry->me_value != NULL ))
            {
                PyObject *old = entry->me_value;
                entry->me_value = value;

                Py_DECREF( old );
            }
            else
            {
                DICT_SET_ITEM( ((PyModuleObject *)_module_%(module_identifier)s)->md_dict, (PyObject *)*this->var_name, value );

                Py_DECREF( value );
            }
        }

        void assign0( PyObject *value ) const
        {
            PyDictEntry *entry = GET_PYDICT_ENTRY( (PyModuleObject *)_module_%(module_identifier)s, *this->var_name );

            // Values are more likely set than not set, in that case speculatively try the
            // quickest access method.
            if (likely( entry->me_value != NULL ))
            {
                PyObject *old = entry->me_value;
                entry->me_value = INCREASE_REFCOUNT( value );

                Py_DECREF( old );
            }
            else
            {
                DICT_SET_ITEM( ((PyModuleObject *)_module_%(module_identifier)s)->md_dict, (PyObject *)*this->var_name, value );
            }
        }

        void del() const
        {
            int status = PyDict_DelItem( ((PyModuleObject *)_module_%(module_identifier)s)->md_dict, (PyObject *)*this->var_name );

            if (unlikely( status == -1 ))
            {
                PyErr_Format( PyExc_NameError, "name '%%s' is not defined", Nuitka_String_AsString( (PyObject *)*this->var_name ) );
                throw _PythonException();
            }
        }

        bool isInitialized( bool allow_builtins = true ) const
        {
            PyDictEntry *entry = GET_PYDICT_ENTRY( (PyModuleObject *)_module_%(module_identifier)s, *this->var_name );

            if (likely( entry->me_value != NULL ))
            {
                return true;
            }

            if ( allow_builtins )
            {
                entry = GET_PYDICT_ENTRY( _module_builtin, *this->var_name );

                return entry->me_value != NULL;
            }
            else
            {
                return false;
            }
        }

    private:
        PyStringObject **var_name;
};

"""

module_body_template = """\
#include "nuitka/prelude.hpp"

#include "__modules.hpp"
#include "__constants.hpp"
#include "__reverses.hpp"

// The _module_%(module_identifier)s is a Python object pointer of module type.

// Note: For full compatability with CPython, every module variable access needs to go
// through it except for cases where the module cannot possibly have changed in the mean
// time.

PyObject *_module_%(module_identifier)s;

// The module level variables.
%(module_globals)s

// The module function declarations.
%(module_functions_decl)s

// The module function definitions.
%(module_functions_code)s

%(expression_temp_decl)s

// Frame object of the module.
static PyFrameObject *frame_%(module_identifier)s;

#ifdef _NUITKA_EXE
static bool init_done = false;
#endif

// The exported interface to CPython. On import of the module, this function gets
// called. It has have that exact function name.

NUITKA_MODULE_INIT_FUNCTION init%(module_identifier)s(void)
{
#ifdef _NUITKA_EXE
    // Packages can be imported recursively in deep executables.
    if ( init_done )
    {
        return;
    }
    else
    {
        init_done = true;
    }
#endif

#ifdef _NUITKA_MODULE
    // In case of a stand alone extension module, need to call initialization the init here
    // because that's how we are going to get called here.

    // Initialize the constant values used.
    _initConstants();

    // Initialize the compiled types of Nuitka.
    PyType_Ready( &Nuitka_Generator_Type );
    PyType_Ready( &Nuitka_Function_Type );
    PyType_Ready( &Nuitka_Method_Type );
    PyType_Ready( &Nuitka_Genexpr_Type );
#endif

    // puts( "in init%(module_identifier)s" );

#ifdef _NUITKA_MODULE
    // Remember it here, Py_InitModule4 will clear it.
    char const *qualified_name = _Py_PackageContext;
#endif

    // Create the module object first. There are no methods initially, all are added
    // dynamically in actual code only.  Also no __doc__ is initially set, as it could not
    // contain 0 this way, added early in actual code.  No self for modules, we have no
    // use for it.
    _module_%(module_identifier)s = Py_InitModule4(
        "%(module_name)s",       // Module Name
        NULL,                    // No methods initially, all are added dynamically in actual code only.
        NULL,                    // No __doc__ is initially set, as it could not contain 0 this way, added early in actual code.
        NULL,                    // No self for modules, we don't use it.
        PYTHON_API_VERSION
    );

    assertObject( _module_%(module_identifier)s );

    // For deep importing of a module we need to have "__builtins__", so we set it
    // ourselves in the same way than CPython does. Note: This must be done before
    // the frame object is allocated, or else it may fail.

    PyObject *module_dict = PyModule_GetDict( _module_%(module_identifier)s );

    if ( PyDict_GetItemString( module_dict, "__builtins__") == NULL )
    {
#ifndef __NUITKA_NO_ASSERT__
        int res =
#endif
            PyDict_SetItemString( module_dict, "__builtins__", PyEval_GetBuiltins() );

        assert( res == 0 );
    }

    frame_%(module_identifier)s = MAKE_FRAME( MAKE_CODEOBJ( %(filename_identifier)s, %(module_name_obj)s, 0, 0 ), _module_%(module_identifier)s);

    // Set module frame as the currently active one.
    FrameGuardLight frame_guard( &frame_%(module_identifier)s );

    // Push the new frame as the currently active one.
    pushFrameStack( frame_%(module_identifier)s );

    // Initialize the standard module attributes.
%(module_inits)s

    // Module code
    bool traceback = false;

    try
    {
        // To restore the initial exception, could be made dependent on actual try/except statement
        // as it is done for functions/classes already.
        FrameExceptionKeeper _frame_exception_keeper;
%(module_code)s
    }
    catch ( _PythonException &_exception )
    {
        if ( !_exception.hasTraceback() )
        {
            _exception.setTraceback( MAKE_TRACEBACK( frame_guard.getFrame() ) );
        }
        else if ( traceback == false )
        {
            _exception.addTraceback( frame_guard.getFrame() );
        }

        _exception.toPython();
    }

    // Pop the frame from the frame stack, we are done here.
    assert( PyThreadState_GET()->frame == frame_%(module_identifier)s );
    PyThreadState_GET()->frame = PyThreadState_GET()->frame->f_back;

    // puts( "out init%(module_identifier)s" );
}
"""

module_init_no_package_template = """\
    _mvar_%(module_identifier)s___doc__.assign0( %(doc_identifier)s );
    _mvar_%(module_identifier)s___file__.assign0( %(filename_identifier)s );
#if %(is_package)d
    _mvar_%(module_identifier)s___path__.assign0( %(path_identifier)s );
#endif

#ifdef _NUITKA_MODULE
    // Set the package attribute from what the import mechanism provided. The package
    // variable should be set for the module code already.
    if ( qualified_name )
    {
        _mvar_%(module_identifier)s___package__.assign0(
            PyString_FromStringAndSize(
               qualified_name,
               strrchr( qualified_name, '.' ) -  qualified_name
            )
        );
    }
#endif"""

module_init_in_package_template = """\
    _mvar_%(module_identifier)s___doc__.assign0( %(doc_identifier)s );
    _mvar_%(module_identifier)s___file__.assign0( %(filename_identifier)s );
#if %(is_package)d
    _mvar_%(module_identifier)s___path__.assign0( %(path_identifier)s );
#endif

    // The package must already be imported.
    assertObject( _module_%(package_identifier)s );

    SET_ATTRIBUTE(
        _module_%(package_identifier)s,
        %(module_name)s,
        _module_%(module_identifier)s
    );
"""

template_header_guard = """\
#ifndef %(header_guard_name)s
#define %(header_guard_name)s

%(header_body)s
#endif
"""

/* -*- Mode: C; c-basic-offset: 4 -*-
 * Kiwi: a Framework and Enhanced Widgets for Python
 *
 * Copyright (C) 2006 Async Open Source
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2.1 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this library; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307
 * USA
 *
 * Author(s): Johan Dahlin <jdahlin@async.com.br>
 */

/* This module contains backports of pygobject/pygtk functions,
 * so we don't have to require the latest versions of them
 */
#include <Python.h>
#include <pygobject.h>
#include <pygtk/pygtk.h>

#if PY_VERSION_HEX < 0x02050000
typedef int Py_ssize_t;
#define PY_SSIZE_T_MAX INT_MAX
#define PY_SSIZE_T_MIN INT_MIN
typedef inquiry lenfunc;
#endif

typedef struct {
    PyObject *func, *data;
} PyGtkCustomNotify;

static void
pygtk_custom_destroy_notify(gpointer user_data)
{
    PyGtkCustomNotify *cunote = user_data;
    PyGILState_STATE state;

    g_return_if_fail(user_data);
    state = pyg_gil_state_ensure();
    Py_XDECREF(cunote->func);
    Py_XDECREF(cunote->data);
    pyg_gil_state_release(state);
    
    g_free(cunote);
}

static gboolean
marshal_emission_hook(GSignalInvocationHint *ihint,
		      guint n_param_values,
		      const GValue *param_values,
		      gpointer user_data)
{
    PyGILState_STATE state;
    gboolean retval = FALSE;
    PyObject *func, *args;
    PyObject *retobj;
    PyObject *params;
    guint i;

    state = pyg_gil_state_ensure();

    /* construct Python tuple for the parameter values */
    params = PyTuple_New(n_param_values);

    for (i = 0; i < n_param_values; i++) {
	PyObject *item = pyg_value_as_pyobject(&param_values[i], FALSE);
	
	/* error condition */
	if (!item) {
	    goto out;
	}
	PyTuple_SetItem(params, i, item);
    }

    args = (PyObject *)user_data;
    func = PyTuple_GetItem(args, 0);
    args = PySequence_Concat(params, PyTuple_GetItem(args, 1));
    Py_DECREF(params);

    /* params passed to function may have extra arguments */

    retobj = PyObject_CallObject(func, args);
    Py_DECREF(args);
    if (retobj == NULL) {
        PyErr_Print();
    }
    
    retval = (retobj == Py_True ? TRUE : FALSE);
    Py_XDECREF(retobj);
out:
    pyg_gil_state_release(state);
    return retval;
}

static PyObject *
pyg_add_emission_hook(PyGObject *self, PyObject *args)
{
    PyObject *first, *callback, *extra_args, *data;
    gchar *name;
    gulong hook_id;
    guint sigid;
    Py_ssize_t len;
    GQuark detail = 0;
    GType gtype;
    PyObject *pygtype;

    len = PyTuple_Size(args);
    if (len < 3) {
	PyErr_SetString(PyExc_TypeError,
			"gobject.add_emission_hook requires at least 3 arguments");
	return NULL;
    }
    first = PySequence_GetSlice(args, 0, 3);
    if (!PyArg_ParseTuple(first, "OsO:add_emission_hook",
			  &pygtype, &name, &callback)) {
	Py_DECREF(first);
	return NULL;
    }
    Py_DECREF(first);
    
    if ((gtype = pyg_type_from_object(pygtype)) == 0) {
	return NULL;
    }
    if (!PyCallable_Check(callback)) {
	PyErr_SetString(PyExc_TypeError, "third argument must be callable");
	return NULL;
    }

    if (!g_signal_parse_name(name, gtype, &sigid, &detail, TRUE)) {
	PyErr_Format(PyExc_TypeError, "%s: unknown signal name: %s",
		     PyString_AsString(PyObject_Repr((PyObject*)self)),
		     name);
	return NULL;
    }
    extra_args = PySequence_GetSlice(args, 3, len);
    if (extra_args == NULL)
	return NULL;

    data = Py_BuildValue("(ON)", callback, extra_args);
    if (data == NULL)
      return NULL;
    
    hook_id = g_signal_add_emission_hook(sigid, detail,
					 marshal_emission_hook,
					 data,
					 (GDestroyNotify)pyg_destroy_notify);
        
    return PyLong_FromUnsignedLong(hook_id);
}

static PyObject *
pyg_remove_emission_hook(PyGObject *self, PyObject *args)
{
    PyObject *pygtype;
    char *name;
    guint signal_id;
    gulong hook_id;
    GType gtype;
    
    if (!PyArg_ParseTuple(args, "Osk:gobject.remove_emission_hook",
			  &pygtype, &name, &hook_id))
	return NULL;
    
    if ((gtype = pyg_type_from_object(pygtype)) == 0) {
	return NULL;
    }
    
    if (!g_signal_parse_name(name, gtype, &signal_id, NULL, TRUE)) {
	PyErr_Format(PyExc_TypeError, "%s: unknown signal name: %s",
		     PyString_AsString(PyObject_Repr((PyObject*)self)),
		     name);
	return NULL;
    }

    g_signal_remove_emission_hook(signal_id, hook_id);
    
    Py_INCREF(Py_None);
    return Py_None;
}

static void
pygdk_event_handler_marshal(GdkEvent *event, gpointer data)
{
    PyGILState_STATE state;
    PyGtkCustomNotify *cunote = data;
    PyObject *retobj;
    PyObject *pyevent;

    g_assert (cunote->func);

    state = pyg_gil_state_ensure();

    pyevent = pyg_boxed_new(GDK_TYPE_EVENT, event, TRUE, TRUE);
    if (cunote->data)
        retobj = PyEval_CallFunction(cunote->func, "(NO)",
				     pyevent, cunote->data);
    else
        retobj = PyEval_CallFunction(cunote->func, "(N)", pyevent);

    if (retobj == NULL) {
        PyErr_Print();
    } else
        Py_DECREF(retobj);

    pyg_gil_state_release(state);
}

static PyObject *
_wrap_gdk_event_handler_set(PyObject *self, PyObject *args, PyObject *kwargs)
{
    PyObject *pyfunc, *pyarg = NULL;
    PyGtkCustomNotify *cunote;

    if (!PyArg_ParseTuple(args, "O|O:event_handler_set",
                          &pyfunc, &pyarg))
        return NULL;

    if (pyfunc == Py_None) {
	gdk_event_handler_set(NULL, NULL, NULL);
    } else {
	cunote = g_new0(PyGtkCustomNotify, 1);
	cunote->func = pyfunc;
	cunote->data = pyarg;
	Py_INCREF(cunote->func);
	Py_XINCREF(cunote->data);

	gdk_event_handler_set(pygdk_event_handler_marshal,
			      cunote,
			      pygtk_custom_destroy_notify);
    }

    Py_INCREF(Py_None);
    return Py_None;
}

static PyMethodDef _kiwi_functions[] = {
    { "add_emission_hook",
      (PyCFunction)pyg_add_emission_hook, METH_VARARGS },
    { "remove_emission_hook",
      (PyCFunction)pyg_remove_emission_hook, METH_VARARGS },
    { "event_handler_set",
      (PyCFunction)_wrap_gdk_event_handler_set, METH_VARARGS },

    { NULL, NULL, 0 }
};

DL_EXPORT(void)
init_kiwi(void)
{

  init_pygobject();
  init_pygtk();
  
  Py_InitModule("kiwi._kiwi", _kiwi_functions);

}

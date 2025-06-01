import {
    LOGIN_REQUEST,
    LOGIN_SUCCESS,
    LOGIN_FAIL,
    USER_LOADED_REQUEST,
    USER_LOADED_SUCCESS,
    USER_LOADED_FAIL,
    AUTHENTICATED_SUCCESS,
    AUTHENTICATED_FAIL,
    PASSWORD_RESET_SUCCESS,
    PASSWORD_RESET_FAIL,
    PASSWORD_RESET_CONFIRM_SUCCESS,
    PASSWORD_RESET_CONFIRM_FAIL,
    SIGNUP_REQUEST,
    SIGNUP_SUCCESS,
    SIGNUP_FAIL,
    ACTIVATION_SUCCESS,
    ACTIVATION_FAIL,
    GOOGLE_AUTH_REQUEST,
    GOOGLE_AUTH_SUCCESS,
    GOOGLE_AUTH_FAIL,
    LOGOUT
} from '../actions/types';

const initialState = {
    access: localStorage.getItem('access'),
    refresh: localStorage.getItem('refresh'),
    loading: false,
    isAuthenticated: null,
    user: null,
    formErrors: null
};

export default function(state = initialState, action) {
    const { type, payload } = action;

    switch(type) {
        case LOGIN_REQUEST:
        case GOOGLE_AUTH_REQUEST: 
        case USER_LOADED_REQUEST:
        case SIGNUP_REQUEST:
            return {
                ...state,
                loading: true
            }
        case AUTHENTICATED_SUCCESS:
            return {
                ...state,
                isAuthenticated: true
            }
        case LOGIN_SUCCESS:
        case GOOGLE_AUTH_SUCCESS:
            localStorage.setItem('access', payload.access);
            localStorage.setItem('refresh', payload.refresh);
            return {
                ...state,
                isAuthenticated: true,
                loading: false,
                access: payload.access,
                refresh: payload.refresh
            }
        case SIGNUP_SUCCESS:
            return {
                ...state,
                loading: false,
                isAuthenticated: false,
                formErrors: null
            }
        case USER_LOADED_SUCCESS:
            return {
                ...state,
                loading: false,
                user: payload
            }
        case AUTHENTICATED_FAIL:
            return {
                ...state,
                isAuthenticated: false
            }
        case USER_LOADED_FAIL:
            return {
                ...state,
                loading: false,
                user: null
            }
        case GOOGLE_AUTH_FAIL:
        case LOGIN_FAIL:
        case SIGNUP_FAIL:
        case LOGOUT:
            localStorage.removeItem('access');
            localStorage.removeItem('refresh');
            localStorage.removeItem('cartData');
            const errors = payload
            const formErrors = {}
            if (errors) {
                Object.keys(errors).forEach(key => {
                    switch (key) {
                      case 'username':
                        formErrors.username = errors[key][0];
                        break;
                      case 'email':
                        formErrors.email = errors[key][0];
                        break;
                      case 'password1':
                        formErrors.password1 = errors[key][0];
                        break;
                      // Handle other Djoser validation errors as needed
                      default:
                        formErrors[key] = errors.detail ? errors.detail : errors[key][0]
                    }
                  });
            }
            
            return {
                ...state,
                access: null,
                refresh: null,
                loading: false,
                isAuthenticated: false,
                user: null,
                formErrors: formErrors
            }
        case PASSWORD_RESET_SUCCESS:
        case PASSWORD_RESET_FAIL:
        case PASSWORD_RESET_CONFIRM_SUCCESS:
        case PASSWORD_RESET_CONFIRM_FAIL:
        case ACTIVATION_SUCCESS:
        case ACTIVATION_FAIL:
            return {
                ...state
            }
        default:
            return state
    }
};

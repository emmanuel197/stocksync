import { combineReducers } from 'redux';
import auth from './auth';
import cart from './cartReducers'
import products from './productReducers'

export default combineReducers({
    auth,
    cart,
    products
});

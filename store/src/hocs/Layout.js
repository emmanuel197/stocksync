import React, { Component } from 'react';
import { connect } from 'react-redux';
import { checkAuthenticated, load_user } from '../actions/auth';
import Navbar from '../components/Navbar';
import { fetchCartData, fetchCookieCart } from '../actions/cartActions';
import { fetchProductsData, fetchProductDetail } from '../actions/productActions';



class Layout extends Component {
    componentDidMount() {
    //     // Call action creators directly without destructure
        this.props.load_user();
        this.props.checkAuthenticated();

        const productsData = JSON.parse(localStorage.getItem('productsData'))
        if (productsData == undefined) { 
            this.props.fetchProductsData()
        }       
    }
    render() {
        const { children } = this.props;

        return (
            <div>
                <Navbar />      
                {children}
            </div>
        );
    }
}

const mapStateToProps = (state) => ({
    isAuthenticated: state.auth.isAuthenticated
  });

export default connect(mapStateToProps, { checkAuthenticated, load_user, fetchCartData, fetchCookieCart, fetchProductsData, fetchProductDetail })(Layout);

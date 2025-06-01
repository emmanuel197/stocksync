import React, { Component } from "react";
import CartProduct from "./CartProduct";
import { connect } from "react-redux";
import { addOrRemoveCookieItem, addOrRemoveItemHandler } from "../actions/cartActions";
class CartPage extends Component {
  constructor(props) {
    super(props);
    this.state = {
      cartUpdated: this.props.cartUpdated
      
    };
    this.updateCart = this.updateCart.bind(this);
    this.checkoutRedirect = this.checkoutRedirect.bind(this)
    this.storeRedirect = this.storeRedirect.bind(this)
    
  }

  

  updateCart(action, product_id) {
    if (this.props.isAuthenticated) {
      this.props.addOrRemoveItemHandler(action, product_id)
    } else {
      this.props.addOrRemoveCookieItem(action, product_id);
    }
  }

  checkoutRedirect() {
    return this.props.history.push('/checkout')
  }

  storeRedirect() {
    return this.props.history.push('/')
  }
  

  render() {
    const styles = {
      float: "right",
      margin: "5px",
    };
    
    const cartProducts = this.props.itemList.map((item) => {
      
      
      return <CartProduct
        id={item.id}
        name={item.product}
        price={item.price}
        image={item.image}
        quantity={item.quantity}
        total={parseFloat(item.total).toFixed(2)}
        updateCart={(action, product_id) => this.updateCart(action, product_id)}
      />}
  );
    return (
      <div className="container">
        <div id="cart-card" className="mt-5">
            <div className="row">
                <div className="col-md-8 cart">
                    <div className="title">
                        <div className="row">
                            <div className="col"><h4><b>Shopping Cart</b></h4></div>
                            <div className="col align-self-center text-right text-muted">{this.props.totalItems} items</div>
                        </div>
                    </div>
                    <hr />
                    {cartProducts} 
      
                    <div className="back-to-shop" style={{cursor: "pointer"}} onClick={this.storeRedirect} ><a style={{textDecoration: "none"}} >&#x2190;</a><span className="text-muted">Back to shop</span></div>
                </div>
                <div className="col-md-4 summary">
                    <div><h5><b>Summary</b></h5></div>
                    <hr/>
                    <div className="row">
                        <div className="col" style={{paddingLeft: "0"}}>ITEMS {this.props.totalItems}</div>
                        <div className="col text-right">$ {parseFloat(this.props.totalCost).toFixed(2)}</div>
                    </div>
                    <form>
                        <p>SHIPPING</p>
                        <select><option className="text-muted">Standard-Delivery- &euro;5.00</option></select>
                        <p>GIVE CODE</p>
                        <input id="code" placeholder="Enter your code"/>
                    </form>
                    <div className="row" style={{borderTop: "1px solid rgba(0,0,0,.1)", padding: "2vh 0"}}>
                        <div className="col">TOTAL PRICE</div>
                        <div className="col text-right">$ {parseFloat(this.props.totalCost).toFixed(2)}</div>
                    </div>
                    <button className="btn btn-color" onClick={this.checkoutRedirect}>CHECKOUT</button>
                </div>
            </div>
            
        </div>
      </div>
    );
  }
}

const mapStateToProps = (state) => ({
  isAuthenticated: state.auth.isAuthenticated,
  totalItems: state.cart.totalItems,
  totalCost: state.cart.totalCost,
  itemList: state.cart.itemList,
});

export default connect(mapStateToProps, {addOrRemoveCookieItem, addOrRemoveItemHandler})(CartPage);

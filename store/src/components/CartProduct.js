import React, { Component } from "react";

export default class CartProduct extends Component {
  constructor(props) {
    super(props);
  }

  render() {
    
    
    return (
    
   
      <div className="row border-bottom">
      <div className="row main align-items-center gy-3">
          <div className="col-lg-3 col-md-6 col-sm-6 col-6"><img className="img-fluid" src={this.props.image}/></div>
          <div className="col-lg-3 col-md-6 col-sm-6 col-6">
              <div title={this.props.name} className="row text-muted text-truncate d-inline-block w-100">{this.props.name}</div>
          </div>
          <div className="col-lg-3 col-md-6 col-sm-6 col-6">
              <a className="update-cart-button" onClick={() => {this.props.updateCart('remove', this.props.id)}}>-</a><a href="#" className="border">{this.props.quantity}</a><a className="update-cart-button" onClick={() => {this.props.updateCart('add', this.props.id)}}>+</a>
          </div>
          <div className="col-lg-3 col-md-6 col-sm-6 col-6">$ {this.props.price} <span className="close">&#10005;</span></div>
      </div>
  </div>
    );
  }
}

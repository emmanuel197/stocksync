import React, { Component } from "react";

export default class CheckoutProduct extends Component {
  constructor(props) {
    super(props);
  }

  render() {
    return (
      <div className="row gy-2">
        <div class="col-lg-6 col-md-6 col-6">
          <div class="row mb-2">
            <div class="col-lg-6 col-md-6 col-12 d-flex justify-content-center">
              <img class="row-image" src={this.props.image} />
            </div>
            <div class="col-lg-6 col-md-6 col-12 d-flex align-items-center justify-content-center">
              <p title={this.props.name} className="text-truncate d-inline-block 
              w-50 text-center">{this.props.name}</p>
            </div>
          </div>
        </div>
        <div class="col-lg-6 col-md-6 col-6 d-flex justify-content-around align-items-center">
          <p>${parseFloat(this.props.total).toFixed(2)}</p>

          <p>x{this.props.quantity}</p>
        </div>

        <div className="px-3">
          <hr />
        </div>
      </div>
    );
  }
}

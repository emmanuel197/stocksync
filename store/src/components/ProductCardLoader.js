import React, { Component } from "react";

class ProductCardLoader extends Component {
  render() {
    return (
      <div className="col-lg-4 col-md-5 product-col">
        <div id="product-wrapper" className="rounded-3">
          <div className="position-relative">
            <div className="image-container">
              <div className="placeholder thumbnail" />
            </div>
            <span
              id="product-badge"
              className="badge  position-absolute"
              style={{ top: "10px", right: "10px" }}
            >
              <div className="placeholder-badge" />
            </span>
          </div>
          <div className="box-element product">
            <h6 className="placeholder-text">
              <strong />
            </h6>
            <hr />
            <div className="row px-2">
              <div className="col-7">
                <div id="placeholder-btn-1" className="rounded"/>
              </div>
              <div className="col-4 px-0">
                <div id="placeholder-btn-2" className="rounded" />
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }
}

export default ProductCardLoader;
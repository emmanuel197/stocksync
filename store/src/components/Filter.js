import React, { Component } from "react";
import ReactSlider from "react-slider";
import {fetchFilteredData, resetProducts} from "../actions/productActions"
import { connect } from "react-redux";

class FilterComponent extends Component {
  constructor(props) {
    super(props);
    this.state = {
      query: "",
      minPrice: 18,
      maxPrice: 400,
      digital: "all",
      activeButton: "apply",
      isCollapsed: {}
    };

    this.handleRadioChange = this.handleRadioChange.bind(this)
    this.handleSliderChange = this.handleSliderChange.bind(this);
    this.applyHandler = this.applyHandler.bind(this)

  }


  handleButtonClick = (buttonId) => {
    this.setState({ activeButton: buttonId });
  };


  applyHandler() {
    const { minPrice, maxPrice, digital } = this.state
    this.props.fetchFilteredData(minPrice, maxPrice, digital)
  }

  handleSliderChange(values) {
    this.setState({ minPrice: values[0], maxPrice: values[1] });
  }
  
  handleRadioChange(event) {
    this.setState({ digital: event.target.value });
  }

  toggleCollapse = (id) => {
    this.setState(prevState => ({
      isCollapsed: {
        ...prevState.isCollapsed,
        [id]: !prevState.isCollapsed[id],
      },
    }));
  };

  renderButton(id) {
    return (
      <button
      id="accordion-btn"
        className="btn ml-auto"
        type="button"
        onClick={() => this.toggleCollapse(id)}
      >
        <span className={`fas ${this.state.isCollapsed[id] ? 'fa-plus' : 'fa-minus'}`}></span>
      </button>
    );
  }

  render() {
    const { minPrice, maxPrice, digital, activeButton } = this.state;

    return (
      <div id="filterbar" class="mt-2 mb-5">
        <div class="box border-bottom">
          <div class="form-group text-center">
            <div class="btn-group" data-toggle="buttons">
              <button
                className={`btn btn-success ${
                  activeButton === "reset" ? "active" : ""
                }`}
                id="reset-btn"
                onClick={() => {
                  this.handleButtonClick("reset")
                  this.props.resetProducts()
                }}
              >
                Reset
              </button>
              <button
                className={`btn btn-success ${
                  activeButton === "apply" ? "active" : ""
                }`}
                id="apply-btn"
                onClick={() => {
                  this.handleButtonClick("apply")
                  this.applyHandler()
                }}
              >
                Apply
              </button>
            </div>
          </div>
        </div>
        <div class="box border-bottom">
          <div class="box-label text-uppercase d-flex align-items-center justify-content-between">
            Product Type
            {this.renderButton("product type")}
          </div>
         {!this.state.isCollapsed["product type"] && <div id="inner-box" class="mt-2 mr-1">
         <div className="row">
              <div className="col-12">
                 <label className="d-flex gap-2">
                    <input
                      type="radio"
                      value="all"
                      checked={digital === "all"}
                      onChange={this.handleRadioChange}
                    />
                    All
                  </label>
                </div>
                <div className="col-12">
                  <label className="d-flex gap-2">
                    <input
                      type="radio"
                      value="true"
                      checked={digital === "true"}
                      onChange={this.handleRadioChange}
                    />
                    Digital
                  </label>
                </div>
                <div className="col-12">
                  <label className="d-flex gap-2">
                    <input
                      type="radio"
                      value="false"
                      checked={digital === "false"}
                      onChange={this.handleRadioChange}
                    />
                    Non-Digital
                  </label>
                </div>
              </div>
          </div>}
        </div>
          <div class="box">
            <div class="box-label text-uppercase d-flex align-items-center justify-content-between">
              price
              {this.renderButton("price")}
            </div>
            {!this.state.isCollapsed["price"] && (
               <>
               <ReactSlider
              className="horizontal-slider"
              thumbClassName="example-thumb"
              trackClassName="example-track"
              min={18}
              max={400}
              minDistance={20}
              defaultValue={[minPrice, maxPrice]}
              onChange={this.handleSliderChange}
            />
            <div>
              Price range: ${minPrice} - ${maxPrice}
            </div></>)}
          </div>
        </div>
    );
  }
}

export default connect(null, {fetchFilteredData, resetProducts})(FilterComponent);

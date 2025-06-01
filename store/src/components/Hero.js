import React, { Component } from "react";
import heroImg from "../../static/images/pexels-albin-biju-6717680.jpg";
class Hero extends Component {
  constructor(props) {
    super(props);
  }

  
  render() {
    
    return (
        <section class="hero">
        <div class="hero__image-wrapper">
          <img
            id="hero__image"
            src={heroImg}
            alt="Picsum placeholder image"
          />
        </div>
        <div class="hero__text">
          <h1>Welcome to Our Store</h1>
          <p>
          Explore our collection of amazing products.
          </p>
          <button id="hero__img-refresh" onClick={this.props.scrollToProducts}>Shop Now</button>
        </div>
      </section>
      
    );
  }
}



export default Hero;

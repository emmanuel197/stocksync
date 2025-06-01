import React, { Component } from 'react';

class Footer extends Component {
    constructor(props) {
        super(props);

    }
    render() {
        return (
                <footer className="text-center text-lg-start text-white mt-5">
                    <section id="footer-section-1" className="d-flex justify-content-between p-4" >
                        <div className="me-5">
                            <span>Get connected with us on social networks:</span>
                        </div>
                        <div>
                            <a href="" className="text-white me-4">
                                <i className="fab fa-facebook-f"></i>
                            </a>
                            <a href="" className="text-white me-4">
                                <i className="fab fa-twitter"></i>
                            </a>
                            <a href="" className="text-white me-4">
                                <i className="fab fa-google"></i>
                            </a>
                            <a href="" className="text-white me-4">
                                <i className="fab fa-instagram"></i>
                            </a>
                            <a href="" className="text-white me-4">
                                <i className="fab fa-linkedin"></i>
                            </a>
                            <a href="" className="text-white me-4">
                                <i className="fab fa-github"></i>
                            </a>
                        </div>
                    </section>
                    <section>
                        <div className="container text-center text-md-start mt-5">
                            <div className="row mt-3">
                                <div className="col-md-3 col-lg-4 col-xl-3 mx-auto mb-4">
                                    <h6 className="text-uppercase fw-bold">KuandorWear</h6>
                                    <hr className="mb-4 mt-0 d-inline-block mx-auto" style={{ width: '60px',  height: '2px' }} />
                                    <p>
                                    Shop stylish and comfortable attire, perfect for every occasion. Whether you’re looking for trendy outfits or timeless classics, we’ve got you covered. Explore our curated collection and elevate your wardrobe today.
                                    </p>
                                </div>
                                <div className="col-md-2 col-lg-2 col-xl-2 mx-auto mb-4">
                                    <h6 className="text-uppercase fw-bold">Products</h6>
                                    <hr className="mb-4 mt-0 d-inline-block mx-auto" style={{ width: '60px',  height: '2px' }} />
                                    <p>
                                        <a href="#!" className="text-white footer-link">T-Shirt</a>
                                    </p>
                                    <p>
                                        <a href="#!" className="text-white footer-link">Watch</a>
                                    </p>
                                    <p>
                                        <a href="#!" className="text-white footer-link">Project Source Code</a>
                                    </p>
                                    <p>
                                        <a href="#!" className="text-white footer-link">Headphones</a>
                                    </p>
                                </div>
                                <div className="col-md-3 col-lg-2 col-xl-2 mx-auto mb-4">
                                    <h6 className="text-uppercase fw-bold">Useful links</h6>
                                    <hr className="mb-4 mt-0 d-inline-block mx-auto" style={{ width: '60px', height: '2px' }} />
                                    <p>
                                        <a href="/cart" className="text-white footer-link">Cart</a>
                                    </p>
                                    <p>
                                        <a href="/checkout" className="text-white footer-link">Checkout</a>
                                    </p>
                                    <p>
                                        <a href="/about" className="text-white footer-link">About Us</a>
                                    </p>
                                    <p>
                                        <a href="#!" className="text-white footer-link">Help</a>
                                    </p>
                                </div>
                                <div className="col-md-4 col-lg-3 col-xl-3 mx-auto mb-md-0 mb-4">
                                    <h6 className="text-uppercase fw-bold">Contact</h6>
                                    <hr className="mb-4 mt-0 d-inline-block mx-auto" style={{ width: '60px', height: '2px' }} />
                                    <p><i className="fas fa-home mr-3"></i> New York, NY 10012, US</p>
                                    <p><i className="fas fa-envelope mr-3"></i> eamokuandoh@gmail.com</p>
                                    <p><i className="fas fa-phone mr-3"></i> + 233 683 6242</p>
                                    <p><i className="fas fa-print mr-3"></i> + 01 234 567 89</p>
                                </div>
                            </div>
                        </div>
                    </section>
                    <div className="text-center p-3" style={{ backgroundColor: 'rgba(0, 0, 0, 0.2)' }}>
                        © 2024 KuandorWear.com
                    </div>
                </footer>
    )}
}

export default Footer;

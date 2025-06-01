import React, { Component } from 'react';
import { Link, withRouter} from 'react-router-dom';
import { connect } from 'react-redux';
import { googleAuthenticate } from '../actions/auth';
import queryString from 'query-string';
import { Redirect } from 'react-router-dom';
class Google extends Component {
    constructor(props) {
        super(props);
        
        this.fetchData = this.fetchData.bind(this)
    }
    
    fetchData() {
        const { googleAuthenticate } = this.props;
        const values = queryString.parse(this.props.location.search);
        const state = values.state ? values.state : null;
        const code = values.code ? values.code : null;

        if (state && code) {
            googleAuthenticate(state, code);
        }
    }
    componentDidMount() {
        this.fetchData()
    }
    componentDidUpdate(prevProps) {
        if (prevProps.location !== this.props.location) {
            this.fetchData()
        }
    }
    render() {
        return (
            // <div className='container'>
            //     <div class='jumbotron mt-5'>
            //         <h1 class='display-4'>Welcome to Auth System!</h1>
            //         <p class='lead'>This is an incredible authentication system with production level features!</p>
            //         <hr class='my-4' />
            //         <p>Click the Log In button</p>
            //         <Link class='btn btn-primary btn-lg' to='/login' role='button'>Login</Link>
            //     </div>
            // </div>
            <Redirect to="/"/>
        );
    }
}

export default withRouter(connect(null, { googleAuthenticate })(Google));

import React from 'react';
import "./Home.css";

function Home() {
    return (
        <div className='home-container'>
            <div className='home-title'>
                <p>Language scanner</p>
            </div>
            <div className='input-output'>
                <div className='input-container'>
                    <textarea className='input-field' placeholder='Start your text here...' type='text' spellCheck='false'></textarea>
                </div>
                <div className='output-container'>
                    <div>
                        <p className='output-title'>Predicted languages:</p>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default Home;
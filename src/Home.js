import React, { useEffect, useState } from 'react';
import "./Home.css";

function Home() {
    const [currentText, setCurrentText] = useState("");
    const [predictions, setPrediction] = useState([]);
    const [updatedText, setUpdatedText] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [loadingText, setLoadingText] = useState("Scanning.");
    const [controller, setController] = useState(null);
    
    // Mudando o texto de Scanning enquanto a requisição é feita
    useEffect(() => {
        if (!isLoading) return;

        const dots = ["Scanning.", "Scanning..", "Scanning..."];
        let index = 0;

        const interval = setInterval(() => {
            setLoadingText(dots[index]);
            index = (index + 1) % dots.length;
        }, 300);

        return () => clearInterval(interval);
    }, [isLoading]);

    // Mudando o updatedText 200ms depois do usuário parar de digitar
    useEffect(() => {
        if (currentText.trim() !== "") {
            setIsLoading(true);
        }

        const handler = setTimeout(() => {
            setUpdatedText(currentText);
        }, 200);

        return () => clearTimeout(handler); 
    }, [currentText]);

    // Fazendo a requisição após o updatedText mudar
    useEffect(() => {
        if (updatedText.trim() === "") {
            setPrediction([]);
            setIsLoading(false);
            return;
        }

        // Se houver uma requisição em andamento, cancela antes de iniciar outra
        if (controller) {
            controller.abort();
        }

        const newController = new AbortController();
        setController(newController);

        const fetchPrediction = async () => {
            setIsLoading(true);

            try {
                const response = await fetch("http://localhost:8000/predict/", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({ text: updatedText }),
                    signal: newController.signal
                });

                if (!response.ok) {
                    throw new Error("Erro ao obter a previsão");
                }

                const data = await response.json();
                setPrediction(data.predictions);
                setIsLoading(false);
            } catch (error) {
                console.error("Erro:", error);
            }
        };

        fetchPrediction();
    }, [updatedText]);

    return (
        <div className='home-container'>
            <div className='home-title'>
                <p>Language scanner</p>
            </div>
            <div className='input-output'>
                <div className='input-container'>
                    <textarea
                        className='input-field'
                        placeholder='Start your text here...'
                        type='text'
                        spellCheck='false'
                        value={currentText}
                        onChange={(e) => setCurrentText(e.target.value)}
                    ></textarea>
                </div>
                <div className='output-container'>
                    <div>
                        <p className='output-title'>Predicted languages:</p>
                        <div className='results'>
                            {isLoading ? (
                                <p className='scanning-text'>{loadingText}</p>
                            ) : (predictions.length > 0 || updatedText !== "") ? (
                                predictions.map((item, index) => (
                                    <div key={index} className='output-result'>
                                        <p>{item[0]}</p>
                                        <p>{item[1]}%</p>
                                    </div>
                                ))
                            ) : (
                                <p>No predictions yet.</p>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default Home;

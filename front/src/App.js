import "./App.css";

function App() {
  return (
    <div className="App">
      <main className="App-main">
        <h3>Analyse automatique de vos documents</h3>
        <input type="file" accept=".pdf" multiple></input>
        <button>Envoyer les documents</button>
      </main>
    </div>
  );
}

export default App;

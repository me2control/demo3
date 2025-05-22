import React, { useState, useEffect } from "react";
import axios from "axios";

function App() {
  const [visitas, setVisitas] = useState([]);
  const [nome, setNome] = useState("");
  const [cpf, setCpf] = useState("");
  const [apartamento, setApartamento] = useState("");
  const [placa, setPlaca] = useState("");
  const [vaga, setVaga] = useState("");
  const [motivo, setMotivo] = useState("Visita");

  const registrarVisita = async () => {
    await axios.post("http://localhost:8000/visitas", {
      nome,
      cpf,
      apartamento,
      placa,
      vaga,
      motivo
    });
    setNome(""); setCpf(""); setApartamento(""); setPlaca(""); setVaga("");
  };

  useEffect(() => {
    const eventSource = new EventSource("http://localhost:8000/stream");
    eventSource.onmessage = (event) => {
      const novaVisita = JSON.parse(event.data);
      setVisitas((prev) => [novaVisita, ...prev]);
    };
    return () => eventSource.close();
  }, []);

  return (
    <div style={{ padding: 20 }}>
      <h1>Cadastro de Visitantes</h1>
      <input placeholder="Nome" value={nome} onChange={(e) => setNome(e.target.value)} /><br/>
      <input placeholder="CPF" value={cpf} onChange={(e) => setCpf(e.target.value)} /><br/>
      <input placeholder="Apartamento" value={apartamento} onChange={(e) => setApartamento(e.target.value)} /><br/>
      <input placeholder="Placa do Veículo" value={placa} onChange={(e) => setPlaca(e.target.value)} /><br/>
      <input placeholder="Vaga Utilizada" value={vaga} onChange={(e) => setVaga(e.target.value)} /><br/>
      <select value={motivo} onChange={(e) => setMotivo(e.target.value)}>
        <option value="Visita">Visita</option>
        <option value="Entrega">Entrega</option>
      </select><br/>
      <button onClick={registrarVisita}>Salvar</button>
      <hr />
      <h2>Visitas Registradas</h2>
      <ul>
        {visitas.map((v, i) => (
          <li key={i}>{v.nome} - {v.motivo}</li>
        ))}
      </ul>
      <footer style={{ marginTop: 40, fontSize: 12 }}>
        Desenvolvido por ME2 Control System Digital.
      </footer>
    </div>
  );
}

export default App;
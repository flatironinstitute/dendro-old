import { BrowserRouter } from 'react-router-dom'
import './App.css'
import MainWindow from './MainWindow'
import GithubAuthSetup from './GithubAuth/GithubAuthSetup'

function App() {
  return (
    <GithubAuthSetup>
      <BrowserRouter>
        <MainWindow />
      </BrowserRouter>
    </GithubAuthSetup>
  )
}

export default App

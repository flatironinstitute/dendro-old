import { BrowserRouter } from 'react-router-dom'
import './App.css'
import MainWindow from './MainWindow'
import GithubAuthSetup from './GithubAuth/GithubAuthSetup'
import { SetupDendro } from './DendroContext/DendroContext'

function App() {
  return (
    <GithubAuthSetup>
      <BrowserRouter>
        <SetupDendro>
          <MainWindow />
        </SetupDendro>
      </BrowserRouter>
    </GithubAuthSetup>
  )
}

export default App

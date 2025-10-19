import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";

function App() {
  const navigate = useNavigate();

  return (
    <div
      className="bg-neutral-800 min-h-screen m-0 p-0 overflow-hidden"
    >
      <motion.div
        className="flex justify-center items-start"
        initial={{ opacity: 0, y: -50 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: "easeOut" }}
      >
          <div className="flex flex-col items-center justify-center h-screen text-center">
          <h1 className="text-6xl text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-500 animate-rgb">ModuLens</h1>
          <p className="text-gray-300 mb-8 text-lg">
            Analyze your Python code's structure and modularity instantly
          </p>
          
          <motion.button
            whileHover={{ scale:1.1 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => navigate("/editor")}
            className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-xl text-lg font-medium"
          >
            Get Started
          </motion.button>
        </div>
      </motion.div>
    </div>
  )
}

export default App

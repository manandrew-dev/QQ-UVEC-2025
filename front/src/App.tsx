import { motion } from "framer-motion";

function App() {

  return (
    <div
      className="bg-neutral-800 min-h-screen m-0 p-0 overflow-hidden"
    >
      <motion.div
        className="mt-[25vh] flex justify-center items-start h-screen"
        initial={{ opacity: 0, y: -50 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: "easeOut" }}
      >
        <h1 className="text-6xl text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-500 animate-rgb">ModuLens</h1>
      </motion.div>
    </div>
  )
}

export default App

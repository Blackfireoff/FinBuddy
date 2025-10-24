import { useState } from "react"
import WalletHealth from "./components/WalletHealth"


function IndexPopup() {
  // This state holds what the user is typing
  const [inputValue, setInputValue] = useState("")

  // This state holds the address after the user hits "submit"
  const [submittedAddress, setSubmittedAddress] = useState("")

  // This function runs when the user submits the form
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault() // Prevents the extension popup from reloading
    setSubmittedAddress(inputValue.trim())
  }

  return (
    <div className="p-4 bg-gray-100" style={{ width: "400px" }}>
      
      {/* --- Input Form --- */}
      <form onSubmit={handleSubmit} className="flex gap-2 mb-4">
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder="Enter ETH Address or ENS"
          className="flex-grow p-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          type="submit"
          className="px-4 py-2 bg-blue-600 text-white rounded-md shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          Go
        </button>
      </form>

      {/* --- Conditional Rendering --- */}
      {/* Only show the WalletHealth component if an address has been submitted */}
      {submittedAddress ? (
        <WalletHealth address={submittedAddress} />
      ) : (
        <p className="text-center text-gray-500">
          Please enter an address to check its health.
        </p>
      )}

    </div>
  )
}

export default IndexPopup
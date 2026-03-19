import React, { useState, useCallback } from "react"
import { cn } from "@/lib/utils"
import { useIsMobile } from "@/hooks/use-mobile"
import { useToast } from "@/hooks/use-toast"
import {
    FileText, Upload, User, Star, ChevronDown,
    ArrowLeft, LogOut, X, Paperclip
} from "lucide-react"

// Types
interface Document {
    id: string
    name: string
    date: string
    isFavorite: boolean
}

type Page = "home" | "login" | "dashboard"

// Auth Modal Component
function AuthModal({
    isOpen,
    onClose,
    onLogin
}: {
    isOpen: boolean;
    onClose: () => void;
    onLogin: () => void;
}) {
    const [email, setEmail] = useState("")
    const [password, setPassword] = useState("")
    const [step, setStep] = useState<"email" | "password">("email")
    const [error, setError] = useState("")

    const isValidEmail = (email: string) => {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
    }

    const handleContinueWithEmail = () => {
        if (!email.trim()) {
            setError("Veuillez entrer votre adresse e-mail")
            return
        }
        if (!isValidEmail(email)) {
            setError("Veuillez entrer une adresse e-mail valide")
            return
        }
        setError("")
        setStep("password")
    }

    const handleLogin = () => {
        if (!password.trim()) {
            setError("Veuillez entrer votre mot de passe")
            return
        }
        if (password.length < 6) {
            setError("Le mot de passe doit contenir au moins 6 caracteres")
            return
        }
        setError("")
        onLogin()
        handleClose()
    }

    const handleGoogleLogin = () => {
        onLogin()
        handleClose()
    }

    const handleClose = () => {
        setEmail("")
        setPassword("")
        setStep("email")
        setError("")
        onClose()
    }

    const handleBack = () => {
        setStep("email")
        setPassword("")
        setError("")
    }

    if (!isOpen) return null

    return (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-3xl p-8 w-full max-w-md shadow-2xl relative">
                <button
                    onClick={handleClose}
                    className="absolute top-4 right-4 text-neutral-400 hover:text-neutral-600 transition-colors"
                >
                    <X className="w-5 h-5" />
                </button>

                {step === "email" ? (
                    <>
                        <h2 className="text-2xl font-medium text-center text-neutral-800 mb-2">
                            Consultez vos documents
                        </h2>
                        <p className="text-neutral-500 text-center mb-8">
                            Inscrivez-vous ou connectez-vous
                        </p>

                        <button
                            onClick={handleGoogleLogin}
                            className="w-full flex items-center justify-center gap-3 border border-neutral-200 rounded-xl py-3.5 px-4 hover:bg-neutral-50 transition-colors mb-6"
                        >
                            <svg className="w-5 h-5" viewBox="0 0 24 24">
                                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                            </svg>
                            <span className="text-neutral-700 font-medium">Continuer avec Google</span>
                        </button>

                        <div className="flex items-center gap-4 mb-6">
                            <div className="flex-1 h-px bg-neutral-200" />
                            <span className="text-neutral-400 text-sm">ou</span>
                            <div className="flex-1 h-px bg-neutral-200" />
                        </div>

                        <div className="space-y-4">
                            <div>
                                <label className="block text-xs font-medium text-neutral-500 uppercase tracking-wider mb-2">
                                    Adresse e-mail
                                </label>
                                <input
                                    type="email"
                                    value={email}
                                    onChange={(e) => { setEmail(e.target.value); setError("") }}
                                    onKeyDown={(e) => e.key === "Enter" && handleContinueWithEmail()}
                                    className="w-full px-4 py-3 bg-neutral-100 rounded-xl border-0 focus:ring-2 focus:ring-neutral-900 transition-all outline-none"
                                    placeholder="vous@exemple.com"
                                    autoFocus
                                />
                            </div>
                            {error && (
                                <p className="text-sm text-red-500">{error}</p>
                            )}
                            <button
                                onClick={handleContinueWithEmail}
                                className="w-full bg-neutral-900 text-white rounded-xl py-3.5 font-medium hover:bg-neutral-800 transition-colors"
                            >
                                Continuer par e-mail
                            </button>
                        </div>
                    </>
                ) : (
                    <>
                        <button
                            onClick={handleBack}
                            className="flex items-center gap-2 text-neutral-500 hover:text-neutral-700 transition-colors mb-6"
                        >
                            <ArrowLeft className="w-4 h-4" />
                            <span className="text-sm">Retour</span>
                        </button>

                        <h2 className="text-2xl font-medium text-center text-neutral-800 mb-2">
                            Entrez votre mot de passe
                        </h2>
                        <p className="text-neutral-500 text-center mb-8">
                            {email}
                        </p>

                        <div className="space-y-4">
                            <div>
                                <label className="block text-xs font-medium text-neutral-500 uppercase tracking-wider mb-2">
                                    Mot de passe
                                </label>
                                <input
                                    type="password"
                                    value={password}
                                    onChange={(e) => { setPassword(e.target.value); setError("") }}
                                    onKeyDown={(e) => e.key === "Enter" && handleLogin()}
                                    className="w-full px-4 py-3 bg-neutral-100 rounded-xl border-0 focus:ring-2 focus:ring-neutral-900 transition-all outline-none"
                                    placeholder="Votre mot de passe"
                                    autoFocus
                                />
                            </div>
                            {error && (
                                <p className="text-sm text-red-500">{error}</p>
                            )}
                            <button
                                onClick={handleLogin}
                                className="w-full bg-neutral-900 text-white rounded-xl py-3.5 font-medium hover:bg-neutral-800 transition-colors"
                            >
                                Se connecter
                            </button>
                            <button className="w-full text-neutral-500 text-sm hover:text-neutral-700 transition-colors">
                                Mot de passe oublie ?
                            </button>
                        </div>
                    </>
                )}
            </div>
        </div>
    )
}

// Login Page Component
function LoginPage({ onNavigate }: { onNavigate: (page: Page) => void }) {
    const [isLogin, setIsLogin] = useState(true)
    const [username, setUsername] = useState("")
    const [password, setPassword] = useState("")

    const handleSubmit = () => {
        onNavigate("dashboard")
    }

    return (
        <div className="min-h-screen bg-neutral-100 flex items-center justify-center p-4">
            <div className="w-full max-w-sm">
                <button
                    onClick={() => onNavigate("home")}
                    className="flex items-center gap-2 text-neutral-500 hover:text-neutral-700 transition-colors mb-8"
                >
                    <ArrowLeft className="w-4 h-4" />
                    <span className="text-sm">Retour</span>
                </button>

                <div className="bg-white rounded-2xl p-8 shadow-sm">
                    <h1 className="text-xl font-medium text-neutral-800 mb-6 text-center">
                        {isLogin ? "Connexion" : "Inscription"}
                    </h1>

                    <div className="space-y-5">
                        <div>
                            <label className="block text-xs font-medium text-neutral-500 uppercase tracking-wider mb-2">
                                Username
                            </label>
                            <input
                                type="text"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                className="w-full px-4 py-3 bg-neutral-50 rounded-xl border border-neutral-200 focus:border-neutral-400 focus:ring-0 transition-colors outline-none"
                            />
                        </div>

                        <div>
                            <label className="block text-xs font-medium text-neutral-500 uppercase tracking-wider mb-2">
                                Password
                            </label>
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="w-full px-4 py-3 bg-neutral-50 rounded-xl border border-neutral-200 focus:border-neutral-400 focus:ring-0 transition-colors outline-none"
                            />
                        </div>
                    </div>

                    <div className="flex gap-3 mt-8">
                        <button
                            onClick={() => setIsLogin(false)}
                            className={`flex-1 py-3 rounded-xl font-medium transition-colors ${!isLogin
                                ? "bg-neutral-900 text-white"
                                : "bg-neutral-100 text-neutral-600 hover:bg-neutral-200"
                                }`}
                        >
                            Inscription
                        </button>
                        <button
                            onClick={handleSubmit}
                            className={`flex-1 py-3 rounded-xl font-medium transition-colors ${isLogin
                                ? "bg-neutral-900 text-white"
                                : "bg-neutral-100 text-neutral-600 hover:bg-neutral-200"
                                }`}
                        >
                            Connexion
                        </button>
                    </div>
                </div>
            </div>
        </div>
    )
}

// Dashboard Page Component
function DashboardPage({ onNavigate, onLogout }: { onNavigate: (page: Page) => void; onLogout: () => void }) {
    const [documents, setDocuments] = useState<Document[]>([
        { id: "1", name: "Facture.pdf", date: "16/03/2026", isFavorite: false },
        { id: "2", name: "Attestation.pdf", date: "15/03/2026", isFavorite: true },
        { id: "3", name: "Contrat.pdf", date: "14/03/2026", isFavorite: false },
    ])
    const [selectedDoc, setSelectedDoc] = useState<Document | null>(documents[0])
    const [showUserMenu, setShowUserMenu] = useState(false)
    const [formData, setFormData] = useState({
        titre: "",
        day: "",
        month: "",
        year: "",
        label1: "",
        label2: "",
        type: "Facture",
    })

    const toggleFavorite = (id: string) => {
        setDocuments(
            documents.map((doc) =>
                doc.id === id ? { ...doc, isFavorite: !doc.isFavorite } : doc
            )
        )
    }

    return (
        <div className="min-h-screen bg-neutral-100">
            {/* Header */}
            <header className="bg-white border-b border-neutral-200">
                <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-neutral-900 rounded-lg flex items-center justify-center">
                            <FileText className="w-5 h-5 text-white" />
                        </div>
                        <span className="font-semibold text-neutral-800">SMYP</span>
                    </div>

                    <div className="relative">
                        <button
                            onClick={() => setShowUserMenu(!showUserMenu)}
                            className="flex items-center gap-2 bg-neutral-900 text-white px-4 py-2 rounded-xl hover:bg-neutral-800 transition-colors"
                        >
                            <User className="w-4 h-4" />
                            <span className="text-sm font-medium">Jean Dupont</span>
                            <ChevronDown className="w-4 h-4" />
                        </button>

                        {showUserMenu && (
                            <div className="absolute right-0 mt-2 w-48 bg-white rounded-xl shadow-lg border border-neutral-200 py-2 z-50">
                                <button className="w-full px-4 py-2 text-left text-sm text-neutral-600 hover:bg-neutral-50 flex items-center gap-2">
                                    <User className="w-4 h-4" />
                                    Mon profil
                                </button>
                                <button
                                    onClick={onLogout}
                                    className="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
                                >
                                    <LogOut className="w-4 h-4" />
                                    Deconnexion
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="max-w-7xl mx-auto px-6 py-8">
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Documents List */}
                    <div className="lg:col-span-1">
                        <div className="bg-white rounded-2xl shadow-sm overflow-hidden">
                            <div className="p-4 border-b border-neutral-100">
                                <h2 className="text-sm font-medium text-neutral-500 uppercase tracking-wider">
                                    Mes documents
                                </h2>
                            </div>

                            <div className="divide-y divide-neutral-100">
                                {documents.map((doc) => (
                                    <button
                                        key={doc.id}
                                        onClick={() => setSelectedDoc(doc)}
                                        className={`w-full p-4 flex items-center gap-3 hover:bg-neutral-50 transition-colors text-left ${selectedDoc?.id === doc.id ? "bg-neutral-50" : ""
                                            }`}
                                    >
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation()
                                                toggleFavorite(doc.id)
                                            }}
                                            className="text-neutral-300 hover:text-amber-400 transition-colors"
                                        >
                                            <Star
                                                className={`w-5 h-5 ${doc.isFavorite ? "fill-amber-400 text-amber-400" : ""
                                                    }`}
                                            />
                                        </button>
                                        <div className="flex-1 min-w-0">
                                            <p className="font-medium text-neutral-800 truncate">
                                                {doc.name}
                                            </p>
                                            <p className="text-sm text-neutral-400">{doc.date}</p>
                                        </div>
                                    </button>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Document Details */}
                    <div className="lg:col-span-2">
                        <div className="bg-white rounded-2xl shadow-sm p-6">
                            <h2 className="text-sm font-medium text-neutral-500 uppercase tracking-wider mb-6">
                                Details du document
                            </h2>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div>
                                    <label className="block text-xs font-medium text-neutral-500 uppercase tracking-wider mb-2">
                                        Titre
                                    </label>
                                    <input
                                        type="text"
                                        value={formData.titre}
                                        onChange={(e) =>
                                            setFormData({ ...formData, titre: e.target.value })
                                        }
                                        className="w-full px-4 py-3 bg-neutral-50 rounded-xl border border-neutral-200 focus:border-neutral-400 focus:ring-0 transition-colors outline-none"
                                        placeholder="Nom du document"
                                    />
                                </div>

                                <div>
                                    <label className="block text-xs font-medium text-neutral-500 uppercase tracking-wider mb-2">
                                        Date
                                    </label>
                                    <div className="flex gap-2">
                                        <input
                                            type="text"
                                            value={formData.day}
                                            onChange={(e) =>
                                                setFormData({ ...formData, day: e.target.value })
                                            }
                                            placeholder="DD"
                                            maxLength={2}
                                            className="w-full px-4 py-3 bg-neutral-50 rounded-xl border border-neutral-200 focus:border-neutral-400 focus:ring-0 transition-colors outline-none text-center"
                                        />
                                        <input
                                            type="text"
                                            value={formData.month}
                                            onChange={(e) =>
                                                setFormData({ ...formData, month: e.target.value })
                                            }
                                            placeholder="MM"
                                            maxLength={2}
                                            className="w-full px-4 py-3 bg-neutral-50 rounded-xl border border-neutral-200 focus:border-neutral-400 focus:ring-0 transition-colors outline-none text-center"
                                        />
                                        <input
                                            type="text"
                                            value={formData.year}
                                            onChange={(e) =>
                                                setFormData({ ...formData, year: e.target.value })
                                            }
                                            placeholder="YYYY"
                                            maxLength={4}
                                            className="w-full px-4 py-3 bg-neutral-50 rounded-xl border border-neutral-200 focus:border-neutral-400 focus:ring-0 transition-colors outline-none text-center"
                                        />
                                    </div>
                                </div>

                                <div>
                                    <label className="block text-xs font-medium text-neutral-500 uppercase tracking-wider mb-2">
                                        Label
                                    </label>
                                    <input
                                        type="text"
                                        value={formData.label1}
                                        onChange={(e) =>
                                            setFormData({ ...formData, label1: e.target.value })
                                        }
                                        className="w-full px-4 py-3 bg-neutral-50 rounded-xl border border-neutral-200 focus:border-neutral-400 focus:ring-0 transition-colors outline-none"
                                        placeholder="Categorie"
                                    />
                                </div>

                                <div>
                                    <label className="block text-xs font-medium text-neutral-500 uppercase tracking-wider mb-2">
                                        Type de fichier
                                    </label>
                                    <select
                                        value={formData.type}
                                        onChange={(e) =>
                                            setFormData({ ...formData, type: e.target.value })
                                        }
                                        className="w-full px-4 py-3 bg-neutral-50 rounded-xl border border-neutral-200 focus:border-neutral-400 focus:ring-0 transition-colors outline-none appearance-none cursor-pointer"
                                    >
                                        <option value="Facture">Facture</option>
                                        <option value="Attestation">Attestation</option>
                                        <option value="Contrat">Contrat</option>
                                        <option value="Autre">Autre</option>
                                    </select>
                                </div>

                                <div className="md:col-span-2">
                                    <label className="block text-xs font-medium text-neutral-500 uppercase tracking-wider mb-2">
                                        Label
                                    </label>
                                    <input
                                        type="text"
                                        value={formData.label2}
                                        onChange={(e) =>
                                            setFormData({ ...formData, label2: e.target.value })
                                        }
                                        className="w-full px-4 py-3 bg-neutral-50 rounded-xl border border-neutral-200 focus:border-neutral-400 focus:ring-0 transition-colors outline-none"
                                        placeholder="Notes additionnelles"
                                    />
                                </div>
                            </div>

                            <div className="mt-8 flex justify-end">
                                <button className="bg-neutral-900 text-white px-6 py-3 rounded-xl font-medium hover:bg-neutral-800 transition-colors">
                                    Enregistrer
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    )
}

// Home Page Component
function HomePage({
    onNavigate,
    onOpenAuth,
    isLoggedIn,
}: {
    onNavigate: (page: Page) => void
    onOpenAuth: () => void
    isLoggedIn: boolean
}) {
    const [isDragging, setIsDragging] = useState(false)
    const [selectedFiles, setSelectedFiles] = useState<File[]>([])

    const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files.length > 0) {
            const newFiles = Array.from(e.target.files)
            setSelectedFiles((prev) => [...prev, ...newFiles])
            // Reset input to allow selecting the same file again
            e.target.value = ""
        }
    }, [])

    const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
        e.preventDefault()
        e.stopPropagation()
        setIsDragging(false)

        if (!isLoggedIn) {
            onOpenAuth()
            return
        }

        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            const newFiles = Array.from(e.dataTransfer.files)
            setSelectedFiles((prev) => [...prev, ...newFiles])
        }
    }, [isLoggedIn, onOpenAuth])

    const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
        e.preventDefault()
        e.stopPropagation()
        if (isLoggedIn) {
            setIsDragging(true)
        }
    }, [isLoggedIn])

    const handleDragLeave = useCallback((e: React.DragEvent<HTMLDivElement>) => {
        e.preventDefault()
        e.stopPropagation()
        setIsDragging(false)
    }, [])

    const handleDropZoneClick = useCallback(() => {
        if (!isLoggedIn) {
            onOpenAuth()
        }
    }, [isLoggedIn, onOpenAuth])

    const removeFile = useCallback((index: number) => {
        setSelectedFiles((prev) => prev.filter((_, i) => i !== index))
    }, [])

    return (
        <div className="min-h-screen bg-neutral-50 flex flex-col">
            {/* Header */}
            <header className="px-6 py-6 grid grid-cols-3 items-center">
                <div></div>

                <div className="flex justify-center">
                    <div className="inline-flex items-center gap-3">
                        <span className="text-3xl font-bold text-neutral-900">SMYP</span>
                        <span className="text-neutral-300 text-xl">-</span>
                        <div className="overflow-hidden max-w-[180px]">
                            <span className="inline-block animate-marquee whitespace-nowrap text-lg text-neutral-600">
                                ShareMeYourPaperasse
                            </span>
                        </div>
                    </div>
                </div>

                <div className="flex justify-end">
                    {isLoggedIn ? (
                        <button
                            onClick={() => onNavigate("dashboard")}
                            className="flex items-center gap-2 bg-neutral-900 text-white px-5 py-2.5 rounded-xl hover:bg-neutral-800 transition-colors"
                        >
                            <User className="w-4 h-4" />
                            <span className="text-sm font-medium">Mon compte</span>
                        </button>
                    ) : (
                        <button
                            onClick={onOpenAuth}
                            className="flex items-center gap-2 bg-neutral-900 text-white px-5 py-2.5 rounded-xl hover:bg-neutral-800 transition-colors"
                        >
                            <User className="w-4 h-4" />
                            <span className="text-sm font-medium">Se connecter</span>
                        </button>
                    )}
                </div>
            </header>

            {/* Main Content */}
            <main className="flex-1 flex items-center justify-center p-6">
                <div className="w-full max-w-md text-center">
                    <h1 className="text-2xl font-medium text-neutral-800 mb-12">
                        Analyse automatique de vos documents
                    </h1>

                    {/* Carre Potier - Drop Zone */}
                    <div
                        onClick={handleDropZoneClick}
                        className={`bg-white rounded-2xl p-8 shadow-sm border-2 border-dashed mb-6 transition-all duration-200 ${!isLoggedIn
                            ? "border-neutral-200 opacity-70 cursor-pointer hover:border-neutral-300"
                            : isDragging
                                ? "border-neutral-900 bg-neutral-100 scale-[1.02]"
                                : "border-neutral-300 hover:border-neutral-400 cursor-default"
                            }`}
                        onDragOver={handleDragOver}
                        onDragLeave={handleDragLeave}
                        onDrop={handleDrop}
                    >
                        <div className={`w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-6 transition-colors ${isDragging ? "bg-neutral-900" : "bg-neutral-100"
                            }`}>
                            <Upload className={`w-8 h-8 transition-colors ${isDragging ? "text-white" : "text-neutral-400"
                                }`} />
                        </div>

                        <p className="text-neutral-500 mb-6">
                            {isDragging
                                ? "Deposez vos fichiers ici..."
                                : "Glissez vos fichiers ici ou cliquez pour selectionner"}
                        </p>

                        {isLoggedIn ? (
                            <label className="cursor-pointer inline-flex items-center gap-2.5 px-5 py-2.5 bg-white border border-neutral-200 rounded-full hover:bg-neutral-50 hover:border-neutral-300 transition-all shadow-sm">
                                <Paperclip className="w-5 h-5 text-neutral-400" />
                                <span className="text-sm font-medium text-neutral-600">Joindre des fichiers</span>
                                <input
                                    type="file"
                                    multiple
                                    onChange={handleFileSelect}
                                    className="hidden"
                                />
                            </label>
                        ) : (
                            <button
                                onClick={onOpenAuth}
                                className="cursor-pointer inline-flex items-center gap-2.5 px-5 py-2.5 bg-white border border-neutral-200 rounded-full hover:bg-neutral-50 hover:border-neutral-300 transition-all shadow-sm"
                            >
                                <Paperclip className="w-5 h-5 text-neutral-400" />
                                <span className="text-sm font-medium text-neutral-600">Joindre des fichiers</span>
                            </button>
                        )}

                        {selectedFiles.length > 0 && (
                            <div className="mt-6 text-left">
                                <p className="text-xs text-neutral-500 uppercase tracking-wider mb-2">
                                    Fichiers selectionnes ({selectedFiles.length})
                                </p>
                                <div className="space-y-2 max-h-40 overflow-y-auto">
                                    {selectedFiles.map((file, index) => (
                                        <div
                                            key={index}
                                            className="flex items-center gap-2 text-sm text-neutral-600 bg-neutral-50 px-3 py-2 rounded-lg"
                                        >
                                            <FileText className="w-4 h-4 flex-shrink-0" />
                                            <span className="truncate flex-1">{file.name}</span>
                                            <span className="text-xs text-neutral-400">
                                                {(file.size / 1024).toFixed(1)} KB
                                            </span>
                                            <button
                                                onClick={(e) => {
                                                    e.stopPropagation()
                                                    removeFile(index)
                                                }}
                                                className="p-1 hover:bg-neutral-200 rounded-md transition-colors"
                                            >
                                                <X className="w-4 h-4 text-neutral-400 hover:text-neutral-600" />
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>

                    {isLoggedIn ? (
                        <button
                            onClick={() => onNavigate("dashboard")}
                            disabled={selectedFiles.length === 0}
                            className={`w-full py-4 rounded-xl font-medium transition-colors ${selectedFiles.length > 0
                                ? "bg-neutral-900 text-white hover:bg-neutral-800"
                                : "bg-neutral-200 text-neutral-400 cursor-not-allowed"
                                }`}
                        >
                            {selectedFiles.length > 0
                                ? `Envoyer ${selectedFiles.length} document${selectedFiles.length > 1 ? "s" : ""}`
                                : "Selectionnez des fichiers"}
                        </button>
                    ) : (
                        <button
                            onClick={onOpenAuth}
                            className="w-full bg-neutral-900 text-white py-4 rounded-xl font-medium hover:bg-neutral-800 transition-colors"
                        >
                            Se connecter pour envoyer
                        </button>
                    )}
                </div>
            </main>
        </div>
    )
}

// Main App Component with Navigation
export default function App() {
    const [currentPage, setCurrentPage] = useState<Page>("home")
    const [showAuthModal, setShowAuthModal] = useState(false)
    const [isLoggedIn, setIsLoggedIn] = useState(false)

    const handleLogin = () => {
        setIsLoggedIn(true)
    }

    const handleLogout = () => {
        setIsLoggedIn(false)
        setCurrentPage("home")
    }

    const renderPage = () => {
        switch (currentPage) {
            case "login":
                return <LoginPage onNavigate={setCurrentPage} />
            case "dashboard":
                return <DashboardPage onNavigate={setCurrentPage} onLogout={handleLogout} />
            default:
                return (
                    <HomePage
                        onNavigate={setCurrentPage}
                        onOpenAuth={() => setShowAuthModal(true)}
                        isLoggedIn={isLoggedIn}
                    />
                )
        }
    }

    return (
        <>
            {renderPage()}
            <AuthModal
                isOpen={showAuthModal}
                onClose={() => setShowAuthModal(false)}
                onLogin={handleLogin}
            />
        </>
    )
}

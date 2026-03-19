import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Header } from '../components/layout/Header'
import { DropZone } from '../components/upload/DropZone'
import { FileList } from '../components/upload/FileList'
import { Modal } from '../components/ui/Modal'
import { Input } from '../components/ui/Input'
import { Button } from '../components/ui/Button'
import { useAuth } from '../hooks/useAuth'
import { useUpload } from '../hooks/useUpload'

type AuthStep = 'email' | 'password'
type AuthMode = 'signin' | 'signup'

export default function Landing() {
  const navigate = useNavigate()
  const { isLoggedIn, isLoading: authLoading, error: authError, signIn, signUp, clearError } = useAuth()
  const { files, isUploading, error: uploadError, addFiles, removeFile, upload } = useUpload()

  const [modalOpen, setModalOpen] = useState(false)
  const [step, setStep] = useState<AuthStep>('email')
  const [mode, setMode] = useState<AuthMode>('signin')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [emailError, setEmailError] = useState('')

  const openModal = () => {
    setStep('email')
    setEmail('')
    setPassword('')
    setEmailError('')
    clearError()
    setModalOpen(true)
  }

  const closeModal = () => {
    setModalOpen(false)
    clearError()
    setEmailError('')
  }

  const handleEmailNext = () => {
    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setEmailError('Adresse email invalide')
      return
    }
    setEmailError('')
    setStep('password')
  }

  const handleAuth = async () => {
    const ok = mode === 'signin'
      ? await signIn(email, password)
      : await signUp(email, password)
    if (ok) {
      closeModal()
      navigate('/dashboard')
    }
  }

  const handleUpload = async () => {
    const ok = await upload()
    if (ok) navigate('/dashboard')
  }

  const handleDropZoneClick = isLoggedIn ? undefined : openModal

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <Header onLoginClick={openModal} />

      <main className="flex-1 flex flex-col items-center justify-center px-4 pt-14">
        <div className="w-full max-w-xl">
          {/* Hero */}
          <div className="text-center mb-10">
            <div className="inline-flex items-center gap-2 rounded-full bg-accent px-3 py-1 mb-5">
              <div className="w-1.5 h-1.5 rounded-full bg-primary" />
              <span className="text-[11px] font-medium uppercase tracking-[0.08em] text-primary">
                Analyse automatique
              </span>
            </div>
            <h1 className="text-3xl font-medium tracking-[-0.02em] text-foreground leading-tight">
              Analysez vos documents
              <br />
              automatiquement
            </h1>
            <p className="mt-3 text-muted-foreground text-base">
              Déposez vos factures, devis et documents administratifs.
              <br />
              SMYP détecte les anomalies en quelques secondes.
            </p>
          </div>

          {/* Drop zone */}
          <DropZone
            onFiles={addFiles}
            onClick={handleDropZoneClick}
          />

          {/* File list */}
          <FileList files={files} onRemove={removeFile} />

          {/* Upload error */}
          {uploadError && (
            <p className="mt-3 text-sm text-destructive text-center">{uploadError}</p>
          )}

          {/* CTA */}
          {isLoggedIn && files.length > 0 && (
            <Button
              className="w-full mt-4"
              size="lg"
              onClick={handleUpload}
              isLoading={isUploading}
            >
              Envoyer {files.length} document{files.length > 1 ? 's' : ''}
            </Button>
          )}

          {!isLoggedIn && files.length > 0 && (
            <Button className="w-full mt-4" size="lg" onClick={openModal}>
              Se connecter pour envoyer {files.length} document{files.length > 1 ? 's' : ''}
            </Button>
          )}
        </div>
      </main>

      {/* Auth Modal */}
      <Modal
        isOpen={modalOpen}
        onClose={closeModal}
        title={mode === 'signin' ? 'Se connecter' : 'Créer un compte'}
      >
        {step === 'email' ? (
          <div className="flex flex-col gap-4">
            <Input
              label="Adresse email"
              id="email"
              type="email"
              placeholder="vous@exemple.fr"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              error={emailError}
              onKeyDown={(e) => e.key === 'Enter' && handleEmailNext()}
              autoFocus
            />
            <Button onClick={handleEmailNext} className="w-full">
              Continuer
            </Button>
            <p className="text-xs text-center text-muted-foreground">
              {mode === 'signin' ? (
                <>
                  Pas encore de compte ?{' '}
                  <button
                    className="text-primary hover:underline font-medium"
                    onClick={() => setMode('signup')}
                  >
                    Créer un compte
                  </button>
                </>
              ) : (
                <>
                  Déjà un compte ?{' '}
                  <button
                    className="text-primary hover:underline font-medium"
                    onClick={() => setMode('signin')}
                  >
                    Se connecter
                  </button>
                </>
              )}
            </p>
          </div>
        ) : (
          <div className="flex flex-col gap-4">
            <div className="flex items-center gap-2 rounded-lg bg-muted px-3 py-2">
              <span className="text-sm text-foreground flex-1">{email}</span>
              <button
                className="text-xs text-primary hover:underline"
                onClick={() => setStep('email')}
              >
                Modifier
              </button>
            </div>
            <Input
              label="Mot de passe"
              id="password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              error={authError ?? undefined}
              onKeyDown={(e) => e.key === 'Enter' && handleAuth()}
              autoFocus
            />
            <Button onClick={handleAuth} isLoading={authLoading} className="w-full">
              {mode === 'signin' ? 'Se connecter' : 'Créer un compte'}
            </Button>
          </div>
        )}
      </Modal>
    </div>
  )
}

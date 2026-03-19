import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ArrowRight,
  CheckCircle2,
  FileWarning,
  ScanSearch,
  ShieldCheck,
  Upload,
  Zap,
} from 'lucide-react'
import { DropZone } from '../components/upload/DropZone'
import { FileList } from '../components/upload/FileList'
import { Modal } from '../components/ui/Modal'
import { Input } from '../components/ui/Input'
import { Button } from '../components/ui/Button'
import { useAuth } from '../hooks/useAuth'
import { useUpload } from '../hooks/useUpload'

type AuthMode = 'signin' | 'signup'

function Counter({ to, suffix = '' }: { to: number; suffix?: string }) {
  const [val, setVal] = useState(0)

  useEffect(() => {
    let current = 0
    const step = Math.ceil(to / 60)
    const id = setInterval(() => {
      current += step
      if (current >= to) {
        setVal(to)
        clearInterval(id)
      } else {
        setVal(current)
      }
    }, 16)
    return () => clearInterval(id)
  }, [to])

  return <>{val.toLocaleString('fr-FR')}{suffix}</>
}

const trustPoints = [
  'PDF, JPG, PNG acceptés',
  'Résultat en moins de 10 sec',
  'Aucune installation',
]

const steps = [
  {
    n: '01',
    label: 'Déposez',
    desc: 'Glissez vos fichiers PDF ou images directement sur la zone de dépôt.',
  },
  {
    n: '02',
    label: 'Analysé',
    desc: 'Notre moteur IA extrait, structure et vérifie chaque champ en quelques secondes.',
  },
  {
    n: '03',
    label: 'Résultat',
    desc: 'Consultez le rapport détaillé avec les anomalies et les données extraites.',
  },
]

const features = [
  {
    icon: FileWarning,
    title: 'Anomalies détectées',
    desc: "Montants incohérents, dates impossibles, champs manquants : rien n'échappe à l'analyse.",
  },
  {
    icon: ScanSearch,
    title: 'OCR intelligent',
    desc: 'Extraction automatique du texte sur vos PDF et images, même scannés ou mal formatés.',
  },
  {
    icon: ShieldCheck,
    title: 'Conformité documentaire',
    desc: 'Vérification des mentions légales obligatoires sur devis, factures et bons de commande.',
  },
  {
    icon: Zap,
    title: 'Résultats en secondes',
    desc: 'Analyse complète délivrée en moins de 10 secondes, sans délai ni export manuel.',
  },
]

const stats = [
  { n: 98, suffix: '%', label: 'Précision OCR' },
  { n: 10, suffix: 's', label: 'Analyse moyenne' },
  { n: 5, suffix: '', label: 'Types de documents' },
  { n: 100, suffix: '%', label: 'Données privées' },
]

export default function Landing() {
  const navigate = useNavigate()
  const uploadSectionRef = useRef<HTMLDivElement>(null)
  const { isLoggedIn, isLoading: authLoading, error: authError, signIn, signUp, clearError } = useAuth()
  const { files, isUploading, error: uploadError, addFiles, removeFile, upload } = useUpload()

  const [modalOpen, setModalOpen] = useState(false)
  const [mode, setMode] = useState<AuthMode>('signin')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const t = setTimeout(() => setVisible(true), 80)
    return () => clearTimeout(t)
  }, [])

  const openModal = () => {
    setEmail('')
    setPassword('')
    clearError()
    setModalOpen(true)
  }

  const closeModal = () => {
    setModalOpen(false)
    clearError()
  }

  const scrollToUpload = () => {
    uploadSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }

  const handleAuth = async () => {
    const ok = mode === 'signin'
      ? await signIn(email, password)
      : await signUp(email, password)
    if (ok) { closeModal(); navigate('/dashboard') }
  }

  const handleUpload = async () => {
    const ok = await upload()
    if (ok) navigate('/dashboard')
  }

  return (
    <>
      <div className="min-h-screen overflow-x-hidden bg-background text-foreground">

        {/* ── Nav ── */}
        <nav className="sticky top-0 z-50 border-b border-border/60 bg-background/90 backdrop-blur-md">
          <div className="mx-auto flex h-14 w-full max-w-6xl items-center justify-between px-6 lg:px-8">
            <a href="/" className="flex items-center gap-2.5 no-underline">
              <img src="/SMYP-logo.png" alt="SMYP" className="h-18 w-auto" />
              <span className="text-sm font-semibold tracking-tight text-foreground">SMYP</span>
            </a>

            <div className="flex items-center gap-2">
              {!isLoggedIn && (
                <>
                  <Button
                    onClick={openModal}
                    variant="secondary"
                    size="sm"
                  >
                    Se connecter
                  </Button>
                  <Button
                    onClick={() => { setMode('signup'); openModal() }}
                    variant="default"
                    size="sm"
                  >
                    Commencer
                    <ArrowRight size={13} />
                  </Button>
                </>
              )}
              {isLoggedIn && (
                <Button
                  onClick={() => navigate('/dashboard')}
                  variant="default"
                  size="sm"
                >
                  Dashboard
                  <ArrowRight size={13} />
                </Button>
              )}
            </div>
          </div>
        </nav>

        <main>

          {/* ── Hero ── */}
          <section
            className={[
              'px-6 pb-24 pt-20 transition-all duration-700 ease-out lg:px-8 lg:pt-28 lg:pb-32',
              visible ? 'translate-y-0 opacity-100' : 'translate-y-5 opacity-0',
            ].join(' ')}
          >
            <div className="mx-auto max-w-6xl">

              {/* Eyebrow */}
              <div className="flex items-center gap-2 mb-10">
                <span className="size-1.5 rounded-full bg-primary" />
                <span className="text-[11px] font-semibold uppercase tracking-[0.18em] text-primary">
                  IA documentaire — analyse en temps réel
                </span>
              </div>

              <div className="grid gap-16 lg:grid-cols-12 lg:items-start lg:gap-12">

                {/* Left: copy */}
                <div className="lg:col-span-6 lg:pb-8">
                  <h1 className="text-[clamp(2.8rem,6vw,4.5rem)] font-semibold leading-[1.02] tracking-[-0.04em] text-foreground">
                    Vos documents.<br />
                    <span className="text-primary">Audités</span> en secondes.
                  </h1>

                  <p className="mt-8 max-w-lg text-[1.05rem] leading-[1.85] text-muted-foreground">
                    Déposez vos factures, devis et documents administratifs.
                    SMYP détecte les anomalies, extrait les données clés et génère
                    un rapport complet — sans friction ni installation.
                  </p>

                  <div className="mt-10 flex flex-wrap gap-3">
                    <Button
                      onClick={() => navigate('/dashboard')}
                      variant="default"
                      size="lg"
                    >
                      Accéder à mon dashboard
                      <ArrowRight size={14} />
                    </Button>
                    {!isLoggedIn && (
                      <Button
                        onClick={openModal}
                        variant="secondary"
                        size="lg"
                      >
                        Se connecter
                      </Button>
                    )}
                  </div>

                  <div className="mt-10 flex flex-wrap gap-x-7 gap-y-3">
                    {trustPoints.map((point) => (
                      <div key={point} className="flex items-center gap-2 text-sm text-muted-foreground">
                        <CheckCircle2 size={14} className="shrink-0 text-primary" />
                        <span>{point}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Right: upload zone */}
                <div ref={uploadSectionRef} className="lg:col-span-6">
                  <div className="rounded-2xl border border-border/70 bg-card shadow-sm">
                    <div className="space-y-5 p-6 sm:p-7">
                      <DropZone onFiles={addFiles} onClick={isLoggedIn ? undefined : openModal} />
                      <FileList files={files} onRemove={removeFile} />

                      {uploadError && (
                        <p className="text-center text-sm text-destructive">{uploadError}</p>
                      )}

                      {isLoggedIn && files.length > 0 && (
                        <Button className="w-full" size="lg" onClick={handleUpload} isLoading={isUploading}>
                          <Upload size={15} />
                          Envoyer {files.length} document{files.length > 1 ? 's' : ''}
                        </Button>
                      )}

                      {!isLoggedIn && files.length > 0 && (
                        <Button className="w-full" size="lg" onClick={openModal}>
                          Se connecter pour envoyer
                        </Button>
                      )}
                    </div>
                  </div>
                </div>

              </div>
            </div>
          </section>

          {/* ── Stats ── */}
          <section className="border-t border-border/60 px-6 py-16 lg:px-8">
            <div className="mx-auto max-w-6xl">
              <div className="grid grid-cols-2 gap-px bg-border/40 overflow-hidden rounded-2xl xl:grid-cols-4">
                {stats.map((stat, i) => (
                  <div
                    key={stat.label}
                    className={[
                      'bg-background px-8 py-10 flex flex-col gap-3',
                      i === 0 ? 'rounded-tl-2xl' : '',
                      i === 1 ? 'xl:rounded-none rounded-tr-2xl' : '',
                      i === 2 ? 'xl:rounded-none rounded-bl-2xl' : '',
                      i === 3 ? 'rounded-br-2xl' : '',
                    ].join(' ')}
                  >
                    <p className="text-[2.6rem] font-semibold leading-none tracking-[-0.04em] text-foreground">
                      <Counter to={stat.n} suffix={stat.suffix} />
                    </p>
                    <p className="text-sm text-muted-foreground">{stat.label}</p>
                  </div>
                ))}
              </div>
            </div>
          </section>

          {/* ── How it works ── */}
          <section className="px-6 py-24 lg:px-8 lg:py-32">
            <div className="mx-auto max-w-6xl">

              <div className="mb-16">
                <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-primary mb-4">
                  Comment ça marche
                </p>
                <h2 className="text-5xl font-semibold tracking-[-0.03em] text-foreground">
                  Trois étapes. Zéro friction.
                </h2>
              </div>

              <div className="grid gap-0 md:grid-cols-3 md:divide-x md:divide-border/60">
                {steps.map((step, i) => (
                  <div
                    key={step.n}
                    className={[
                      'py-10 md:px-10 flex flex-col gap-6',
                      i > 0 ? 'border-t border-border/60 md:border-t-0' : '',
                      i === 0 ? 'md:pl-0' : '',
                      i === steps.length - 1 ? 'md:pr-0' : '',
                    ].join(' ')}
                  >
                    <span className="font-mono text-[11px] font-bold tracking-[0.12em] text-primary/60">
                      {step.n}
                    </span>
                    <div>
                      <h3 className="text-xl font-semibold tracking-[-0.02em] text-foreground mb-3">
                        {step.label}
                      </h3>
                      <p className="text-sm leading-7 text-muted-foreground max-w-xs">
                        {step.desc}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </section>

          {/* ── Features ── */}
          <section className="border-t border-border/60 bg-muted/30 px-6 py-24 lg:px-8 lg:py-32">
            <div className="mx-auto max-w-6xl">

              <div className="mb-16 max-w-lg">
                <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-primary mb-4">
                  Fonctionnalités
                </p>
                <h2 className="text-5xl font-semibold tracking-[-0.03em] text-foreground">
                  Ce que SMYP détecte pour vous
                </h2>
                <p className="mt-5 text-sm leading-7 text-muted-foreground">
                  OCR, contrôle documentaire et détection d'incohérences travaillent ensemble
                  pour produire un résultat lisible immédiatement.
                </p>
              </div>

              <div className="grid gap-px bg-border/40 overflow-hidden rounded-2xl md:grid-cols-2">
                {features.map(({ icon: Icon, title, desc }, i) => (
                  <div
                    key={title}
                    className={[
                      'bg-background p-8 flex gap-5',
                      i === 0 ? 'rounded-tl-2xl' : '',
                      i === 1 ? 'rounded-tr-2xl' : '',
                      i === features.length - 2 ? 'rounded-bl-2xl' : '',
                      i === features.length - 1 ? 'rounded-br-2xl' : '',
                    ].join(' ')}
                  >
                    <div className="shrink-0 mt-0.5">
                      <div className="flex size-9 items-center justify-center rounded-xl bg-primary/10 text-primary">
                        <Icon size={17} />
                      </div>
                    </div>
                    <div>
                      <h3 className="text-base font-semibold tracking-[-0.02em] text-foreground mb-2">
                        {title}
                      </h3>
                      <p className="text-sm leading-7 text-muted-foreground">{desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </section>

          {/* ── CTA ── */}
          <section className="px-6 py-24 lg:px-8 lg:py-32">
            <div className="mx-auto max-w-6xl">
              <div className="flex flex-col gap-10 lg:flex-row lg:items-end lg:justify-between">
                <div className="max-w-2xl">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-primary mb-5">
                    Prêt à commencer ?
                  </p>
                  <h2 className="text-5xl font-semibold tracking-[-0.04em] text-foreground">
                    Analysez votre premier<br />
                    document gratuitement.
                  </h2>
                  <p className="mt-6 text-sm leading-7 text-muted-foreground">
                    Aucune carte bancaire requise. Déposez un fichier et obtenez votre
                    analyse complète en quelques secondes.
                  </p>
                </div>

                <Button
                  onClick={scrollToUpload}
                  variant="default"
                  size="lg"
                >
                  Démarrer gratuitement
                  <ArrowRight size={14} />
                </Button>
              </div>
            </div>
          </section>

        </main>

        {/* ── Footer ── */}
        <footer className="border-t border-border/60 px-6 py-8 lg:px-8">
          <div className="mx-auto flex max-w-6xl flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold text-foreground">SMYP</span>
              <span className="text-border">·</span>
              <span className="text-sm text-muted-foreground">ShareMeYourPaperasse</span>
            </div>
            <p className="text-xs text-muted-foreground">© 2026 SMYP — Tous droits réservés</p>
          </div>
        </footer>
      </div>

      {/* ── Auth modal ── */}
      <Modal
        isOpen={modalOpen}
        onClose={closeModal}
        title={mode === 'signin' ? 'Se connecter' : 'Créer un compte'}
      >
        <div className="flex flex-col gap-4">
          <Input
            label="Adresse email"
            id="email"
            type="email"
            placeholder="vous@exemple.fr"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoFocus
          />
          <Input
            label="Mot de passe"
            id="password"
            type="password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            error={authError ?? undefined}
            onKeyDown={(e) => e.key === 'Enter' && handleAuth()}
          />
          <Button onClick={handleAuth} isLoading={authLoading} className="w-full">
            {mode === 'signin' ? 'Se connecter' : 'Créer un compte'}
          </Button>
          <p className="text-center text-xs text-muted-foreground">
            {mode === 'signin' ? (
              <>
                Pas encore de compte ?{' '}
                <button
                  className="font-medium text-primary hover:underline"
                  onClick={() => { setMode('signup'); clearError() }}
                >
                  Créer un compte
                </button>
              </>
            ) : (
              <>
                Déjà un compte ?{' '}
                <button
                  className="font-medium text-primary hover:underline"
                  onClick={() => { setMode('signin'); clearError() }}
                >
                  Se connecter
                </button>
              </>
            )}
          </p>
        </div>
      </Modal>
    </>
  )
}

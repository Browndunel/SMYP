import { create } from 'zustand'
import type { Document, DocumentsStore } from '../types'

export const useDocumentsStore = create<DocumentsStore>()((set) => ({
  documents: [],
  isLoading: false,
  setDocuments: (docs: Document[]) => set({ documents: docs }),
  addDocuments: (docs: Document[]) =>
    set((state) => ({ documents: [...docs, ...state.documents] })),
  removeDocument: (id: string) =>
    set((state) => ({ documents: state.documents.filter((d) => d.id !== id) })),
  setLoading: (loading: boolean) => set({ isLoading: loading }),
}))

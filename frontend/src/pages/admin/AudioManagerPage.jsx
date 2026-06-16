import { useState, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { audioService, instrumentsService } from "../../services/api";
import toast from "react-hot-toast";
import {
  ArrowUpTrayIcon, SpeakerWaveIcon, TrashIcon, PencilIcon,
  MagnifyingGlassIcon, MusicalNoteIcon,
} from "@heroicons/react/24/outline";
import useAuthStore from "../../store/authStore";
import { Navigate } from "react-router-dom";

function UploadModal({ instruments, notes, onClose, onSuccess }) {
  const fileRef = useRef();
  const [file, setFile] = useState(null);
  const [form, setForm] = useState({ instrument_id: "", note_id: "", difficulty: "intermedio", description: "", tags: "" });
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return toast.error("Selecciona un archivo");

    const formData = new FormData();
    formData.append("file", file);
    Object.entries(form).forEach(([k, v]) => v && formData.append(k, v));

    setUploading(true);
    try {
      await audioService.upload(formData, (e) => {
        setProgress(Math.round((e.loaded / e.total) * 100));
      });
      toast.success("Audio subido exitosamente");
      onSuccess();
      onClose();
    } catch (err) {
      toast.error(err.response?.data?.error || "Error al subir audio");
    } finally {
      setUploading(false);
      setProgress(0);
    }
  };

  const DIFFICULTIES = ["principiante", "basico", "intermedio", "avanzado", "experto"];

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-gray-800 rounded-2xl w-full max-w-md p-6 shadow-2xl">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-5">Subir Audio</h2>
        <form onSubmit={handleUpload} className="space-y-4">
          <div
            onClick={() => fileRef.current?.click()}
            className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-xl p-6 text-center cursor-pointer hover:border-primary-400 transition-colors"
          >
            <ArrowUpTrayIcon className="h-8 w-8 mx-auto text-gray-400 mb-2" />
            {file ? (
              <p className="font-medium text-primary-700">{file.name}</p>
            ) : (
              <>
                <p className="font-medium text-gray-700 dark:text-gray-300">Arrastra o selecciona un archivo</p>
                <p className="text-xs text-gray-500 mt-1">WAV, MP3, OGG, FLAC — máx 50MB</p>
              </>
            )}
            <input
              ref={fileRef}
              type="file"
              accept=".wav,.mp3,.ogg,.flac"
              className="hidden"
              onChange={(e) => setFile(e.target.files[0])}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Instrumento</label>
              <select className="input-field text-sm" value={form.instrument_id} onChange={(e) => setForm({ ...form, instrument_id: e.target.value })}>
                <option value="">Todos</option>
                {instruments?.map((i) => <option key={i.id} value={i.id}>{i.name}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Nota</label>
              <select className="input-field text-sm" value={form.note_id} onChange={(e) => setForm({ ...form, note_id: e.target.value })}>
                <option value="">Sin nota</option>
                {notes?.map((n) => <option key={n.id} value={n.id}>{n.scientific_name}</option>)}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Dificultad</label>
            <select className="input-field text-sm" value={form.difficulty} onChange={(e) => setForm({ ...form, difficulty: e.target.value })}>
              {DIFFICULTIES.map((d) => <option key={d} value={d}>{d}</option>)}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Descripción</label>
            <input className="input-field text-sm" placeholder="Descripción opcional" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Tags (separados por coma)</label>
            <input className="input-field text-sm" placeholder="andino,colombiano,tradicional" value={form.tags} onChange={(e) => setForm({ ...form, tags: e.target.value })} />
          </div>

          {uploading && (
            <div>
              <div className="progress-bar">
                <div className="progress-fill" style={{ width: `${progress}%` }} />
              </div>
              <p className="text-xs text-gray-500 text-center mt-1">{progress}%</p>
            </div>
          )}

          <div className="flex gap-3">
            <button type="button" onClick={onClose} className="btn-ghost flex-1" disabled={uploading}>Cancelar</button>
            <button type="submit" disabled={uploading || !file} className="btn-primary flex-1">
              {uploading ? "Subiendo..." : "Subir audio"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function AudioManagerPage() {
  const user = useAuthStore((s) => s.user);
  if (!["admin", "instructor"].includes(user?.role)) {
    return <Navigate to="/dashboard" replace />;
  }

  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [filterInstrument, setFilterInstrument] = useState("");
  const [showUpload, setShowUpload] = useState(false);
  const [playing, setPlaying] = useState(null);
  const audioRef = useRef(null);
  const qc = useQueryClient();

  const { data: instruments } = useQuery({ queryKey: ["instruments"], queryFn: () => instrumentsService.list().then((r) => r.data) });
  const { data: notes } = useQuery({ queryKey: ["notes"], queryFn: () => instrumentsService.notes().then((r) => r.data) });
  const { data, isLoading } = useQuery({
    queryKey: ["audios", page, search, filterInstrument],
    queryFn: () => audioService.list({ page, per_page: 12, search, instrument_id: filterInstrument || undefined }).then((r) => r.data),
  });

  const deleteMutation = useMutation({
    mutationFn: (id) => audioService.delete(id),
    onSuccess: () => { toast.success("Audio eliminado"); qc.invalidateQueries(["audios"]); },
    onError: () => toast.error("Error al eliminar"),
  });

  const handlePlay = (audio) => {
    if (!audioRef.current) return;
    if (playing === audio.id) {
      audioRef.current.pause();
      setPlaying(null);
      return;
    }
    audioRef.current.src = audio.url_path;
    audioRef.current.play();
    setPlaying(audio.id);
  };

  return (
    <div className="space-y-6">
      <audio ref={audioRef} onEnded={() => setPlaying(null)} />

      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h1 className="section-title">Banco de Audio</h1>
          <p className="section-subtitle">Gestiona los archivos de audio del sistema</p>
        </div>
        <button onClick={() => setShowUpload(true)} className="btn-primary flex items-center gap-2">
          <ArrowUpTrayIcon className="h-4 w-4" />
          Subir audio
        </button>
      </div>

      <div className="flex gap-3 flex-wrap">
        <div className="relative flex-1 min-w-48">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            className="input-field pl-9"
            placeholder="Buscar audios..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          />
        </div>
        <select className="input-field w-auto" value={filterInstrument} onChange={(e) => { setFilterInstrument(e.target.value); setPage(1); }}>
          <option value="">Todos los instrumentos</option>
          {instruments?.map((i) => <option key={i.id} value={i.id}>{i.name}</option>)}
        </select>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-16">
          <div className="w-8 h-8 border-4 border-primary-200 border-t-primary-700 rounded-full animate-spin" />
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {data?.audios?.map((audio) => (
              <div key={audio.id} className="card p-4 group hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between gap-2 mb-3">
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-sm text-gray-900 dark:text-white truncate" title={audio.original_filename}>
                      {audio.original_filename}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                      {audio.instrument?.name} {audio.note ? `• ${audio.note.scientific_name}` : ""}
                    </p>
                  </div>
                  <span className="badge-primary text-xs flex-shrink-0">{audio.difficulty}</span>
                </div>

                <div className="flex items-center gap-1 text-xs text-gray-400 mb-3">
                  <MusicalNoteIcon className="h-3.5 w-3.5" />
                  <span>{audio.duration ? `${audio.duration.toFixed(1)}s` : "—"}</span>
                  <span>•</span>
                  <span>{audio.sample_rate ? `${audio.sample_rate / 1000}kHz` : "—"}</span>
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={() => handlePlay(audio)}
                    className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-sm font-medium transition-all ${
                      playing === audio.id
                        ? "bg-primary-900 text-white"
                        : "bg-primary-100 text-primary-700 hover:bg-primary-200 dark:bg-primary-900/30 dark:text-primary-400"
                    }`}
                  >
                    <SpeakerWaveIcon className="h-4 w-4" />
                    {playing === audio.id ? "Pausar" : "Escuchar"}
                  </button>
                  <button
                    onClick={() => deleteMutation.mutate(audio.id)}
                    className="p-2 rounded-lg text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                    title="Eliminar"
                  >
                    <TrashIcon className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>

          {data?.audios?.length === 0 && (
            <div className="text-center py-16 card">
              <SpeakerWaveIcon className="h-16 w-16 mx-auto text-gray-200 dark:text-gray-600 mb-4" />
              <h3 className="font-semibold text-gray-700 dark:text-gray-300">Sin audios</h3>
              <p className="text-sm text-gray-400 mt-1">Sube el primer archivo de audio</p>
            </div>
          )}

          {data?.pages > 1 && (
            <div className="flex justify-center gap-2">
              {[...Array(data.pages)].map((_, i) => (
                <button
                  key={i}
                  onClick={() => setPage(i + 1)}
                  className={`w-9 h-9 rounded-lg text-sm font-medium transition-colors ${
                    page === i + 1 ? "bg-primary-900 text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300"
                  }`}
                >
                  {i + 1}
                </button>
              ))}
            </div>
          )}
        </>
      )}

      {showUpload && (
        <UploadModal
          instruments={instruments}
          notes={notes}
          onClose={() => setShowUpload(false)}
          onSuccess={() => qc.invalidateQueries(["audios"])}
        />
      )}
    </div>
  );
}

import jsPDF from "jspdf";
import { ResultatOptimisation } from "@/types";

export function exporterPlanningPDF(resultat: ResultatOptimisation, heureDebut: string, heureFin: string) {
  const doc = new jsPDF();
  
  // Configuration de la police
  doc.setFont("helvetica", "normal");
  
  // Fonction pour nettoyer et normaliser le texte
  const cleanText = (text: string): string => {
    return text
      .normalize("NFD") // Décompose les caractères accentués
      .replace(/[\u0300-\u036f]/g, "") // Supprime les diacritiques
      .replace(/'/g, "'") // Apostrophe droite
      .replace(/"/g, '"') // Guillemets droits
      .replace(/\s+/g, " ") // Normalise espaces
      .trim();
  };
  
  // Mapping des priorités vers des libellés lisibles
  const getPrioriteLabel = (priorite: number): string => {
    const labels: Record<number, string> = {
      1: "Tres basse priorite",
      2: "Basse priorite",
      3: "Priorite moyenne",
      4: "Haute priorite",
      5: "Tres haute priorite"
    };
    return labels[priorite] || `Priorite ${priorite}`;
  };
  
  // --- EN-TÊTE ---
  doc.setFontSize(22);
  doc.setTextColor(79, 70, 229);
  doc.text("Planning Optimise", 20, 25);
  
  doc.setFontSize(10);
  doc.setTextColor(120, 120, 120);
  const dateStr = new Date().toLocaleDateString("fr-FR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric"
  });
  doc.text(`Genere par TaskOptimizer - ${dateStr}`, 20, 35);
  
  // --- SÉPARATEUR ---
  doc.setDrawColor(220, 220, 220);
  doc.setLineWidth(0.5);
  doc.line(20, 45, 190, 45);
  
  // --- MÉTRIQUES ---
  const startY = 60;
  doc.setFontSize(11);
  doc.setTextColor(60, 60, 60);
  
  doc.text(`Horaires : ${heureDebut} a ${heureFin}`, 20, startY);
  doc.text(`Score d'optimisation : ${resultat.score_optimisation}%`, 20, startY + 12);
  doc.text(`Temps planifie : ${formatTemps(resultat.temps_total_planifie)}`, 20, startY + 24);
  
  // --- MESSAGE ---
  doc.setDrawColor(220, 220, 220);
  doc.line(20, startY + 38, 190, startY + 38);
  
  doc.setFontSize(10);
  doc.setTextColor(100, 100, 100);
  const messageLines = doc.splitTextToSize(cleanText(resultat.message), 170);
  doc.text(messageLines, 20, startY + 48);
  
  const messageHeight = messageLines.length * 5;
  
  // --- PLANNING ---
  const planningStartY = startY + 60 + messageHeight;
  doc.setDrawColor(220, 220, 220);
  doc.line(20, planningStartY - 10, 190, planningStartY - 10);
  
  doc.setFontSize(14);
  doc.setTextColor(50, 50, 50);
  doc.setFont("helvetica", "bold");
  doc.text("Planning Journalier", 20, planningStartY);
  doc.setFont("helvetica", "normal");
  
  // En-têtes de colonnes
  doc.setFontSize(9);
  doc.setTextColor(100, 100, 100);
  doc.setFont("helvetica", "bold");
  doc.text("Heure", 20, planningStartY + 15);
  doc.text("Activite", 60, planningStartY + 15);
  doc.text("Priorite", 125, planningStartY + 15);
  doc.setFont("helvetica", "normal");
  
  doc.setDrawColor(230, 230, 230);
  doc.line(20, planningStartY + 22, 190, planningStartY + 22);
  
  let y = planningStartY + 32;
  doc.setFontSize(10);
  
  resultat.planning.forEach((plage) => {
    if (y > 260) {
      doc.addPage();
      y = 25;
      
      // Répéter l'en-tête sur la nouvelle page
      doc.setFontSize(14);
      doc.setTextColor(50, 50, 50);
      doc.setFont("helvetica", "bold");
      doc.text("Planning Journalier (suite)", 20, y);
      doc.setFont("helvetica", "normal");
      
      doc.setFontSize(9);
      doc.setTextColor(100, 100, 100);
      doc.setFont("helvetica", "bold");
      doc.text("Heure", 20, y + 15);
      doc.text("Activite", 60, y + 15);
      doc.text("Priorite", 125, y + 15);
      doc.setFont("helvetica", "normal");
      
      doc.setDrawColor(230, 230, 230);
      doc.line(20, y + 22, 190, y + 22);
      y += 32;
    }
    
    doc.setTextColor(50, 50, 50);
    doc.text(`${plage.debut} - ${plage.fin}`, 20, y);
    doc.text(cleanText(plage.activite), 60, y);
    doc.setTextColor(100, 100, 100);
    doc.setFontSize(8);
    const prioriteLabel = getPrioriteLabel(plage.priorite);
    doc.text(`${prioriteLabel} (P${plage.priorite})`, 125, y);
    doc.setFontSize(10);
    doc.setTextColor(50, 50, 50);
    
    y += 10;
  });
  
  // --- ACTIVITÉS NON PLANIFIÉES ---
  if (resultat.activites_non_planifiees.length > 0) {
    if (y > 230) {
      doc.addPage();
      y = 25;
    }
    
    y += 10;
    doc.setDrawColor(220, 220, 220);
    doc.line(20, y, 190, y);
    y += 15;
    
    doc.setFontSize(12);
    doc.setTextColor(180, 80, 80);
    doc.setFont("helvetica", "bold");
    doc.text("Activites Non Planifiees", 20, y);
    doc.setFont("helvetica", "normal");
    
    y += 15;
    doc.setFontSize(10);
    doc.setTextColor(100, 100, 100);
    
    resultat.activites_non_planifiees.forEach((nom) => {
      doc.text(`- ${cleanText(nom)}`, 25, y);
      y += 8;
    });
  }
  
  // --- PIED DE PAGE ---
  const pageCount = (doc as unknown as { internal: { getNumberOfPages: () => number } }).internal.getNumberOfPages();
  for (let i = 1; i <= pageCount; i++) {
    doc.setPage(i);
    doc.setFontSize(8);
    doc.setTextColor(180, 180, 180);
    doc.text(`Page ${i} / ${pageCount}`, 20, 285);
    doc.text("TaskOptimizer - Moteur CP-SAT", 190, 285, { align: "right" });
  }
  
  doc.save(`planning-${new Date().toISOString().split("T")[0]}.pdf`);
}

function formatTemps(minutes: number): string {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return m > 0 ? `${h}h ${m}min` : `${h}h`;
}

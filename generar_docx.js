/**
 * MonografiasBot1 — Generador de .docx académico
 * Formato: Times New Roman 12pt, doble espacio, sangría 1.27cm, alineación izquierda
 */

const {
  Document, Packer, Paragraph, TextRun, HeadingLevel,
  AlignmentType, PageNumber, Footer, Header,
  NumberFormat, convertInchesToTwip, LevelFormat,
  TableOfContents, PageBreak
} = require('docx');
const fs   = require('fs');
const path = require('path');

// ── Leer datos desde JSON ─────────────────────────────────────────────────────
const jsonPath = process.argv[2];
if (!jsonPath) { console.error('Falta argumento JSON'); process.exit(1); }
const datos = JSON.parse(fs.readFileSync(jsonPath, 'utf8'));

const {
  tema, curso, especialidad, nivel, paginas,
  introduccion, desarrollo, conclusiones, referencias, salida
} = datos;

// ── Constantes de formato ─────────────────────────────────────────────────────
const FONT          = 'Times New Roman';
const SIZE_BODY     = 24;        // 12pt en half-points
const SIZE_H1       = 28;        // 14pt
const SIZE_H2       = 24;        // 12pt bold
const SIZE_TITLE    = 32;        // 16pt portada
const LINE_SPACING  = 480;       // doble espacio (240 = simple, 480 = doble)
const INDENT_LEFT   = 720;       // 1.27 cm en DXA (1 cm = ~567 DXA, 1.27cm ≈ 720)
const HANGING_REF   = 720;       // sangría francesa para referencias
const MARGIN        = 1440;      // 1 pulgada en DXA
const anio          = new Date().getFullYear();

// ── Helpers ───────────────────────────────────────────────────────────────────

/** Párrafo de cuerpo con doble espacio, sangría izquierda 1.27cm, alineación izquierda */
function parrafo(texto, opciones = {}) {
  if (!texto || !texto.trim()) return null;
  return new Paragraph({
    alignment: AlignmentType.LEFT,
    spacing: { line: LINE_SPACING, lineRule: 'auto', before: 0, after: 120 },
    indent: { left: INDENT_LEFT },
    children: [
      new TextRun({
        text: texto.trim(),
        font: FONT,
        size: SIZE_BODY,
        bold: opciones.bold || false,
        italics: opciones.italics || false,
      })
    ],
    ...opciones.extraProps
  });
}

/** Heading 1 — sección principal (INTRODUCCIÓN, DESARROLLO, etc.) */
function heading1(texto) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    alignment: AlignmentType.LEFT,
    spacing: { line: LINE_SPACING, before: 480, after: 240 },
    indent: { left: 0 },
    children: [new TextRun({ text: texto.toUpperCase(), font: FONT, size: SIZE_H1, bold: true })]
  });
}

/** Heading 2 — capítulos y subsecciones */
function heading2(texto) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    alignment: AlignmentType.LEFT,
    spacing: { line: LINE_SPACING, before: 360, after: 180 },
    indent: { left: INDENT_LEFT },
    children: [new TextRun({ text: texto, font: FONT, size: SIZE_H2, bold: true })]
  });
}

/** Heading 3 — subcapítulos (1.1, 1.2...) */
function heading3(texto) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    alignment: AlignmentType.LEFT,
    spacing: { line: LINE_SPACING, before: 240, after: 120 },
    indent: { left: INDENT_LEFT },
    children: [new TextRun({ text: texto, font: FONT, size: SIZE_BODY, bold: true, italics: true })]
  });
}

/** Salto de página */
function saltoPagina() {
  return new Paragraph({
    children: [new PageBreak()],
    spacing: { line: LINE_SPACING }
  });
}

/** Línea vacía */
function linea() {
  return new Paragraph({
    children: [new TextRun({ text: '', font: FONT, size: SIZE_BODY })],
    spacing: { line: LINE_SPACING }
  });
}

/** Párrafo de referencia bibliográfica con sangría francesa */
function parrafoRef(texto) {
  if (!texto || !texto.trim()) return null;
  return new Paragraph({
    alignment: AlignmentType.LEFT,
    spacing: { line: LINE_SPACING, before: 0, after: 120 },
    indent: { left: INDENT_LEFT + HANGING_REF, hanging: HANGING_REF },
    children: [new TextRun({ text: texto.trim(), font: FONT, size: SIZE_BODY })]
  });
}

/** Convierte texto largo en array de párrafos, detectando headings */
function textoParagrafos(texto) {
  if (!texto) return [];
  const lineas = texto.split('\n');
  const result = [];

  for (const ln of lineas) {
    const t = ln.trim();
    if (!t) { result.push(linea()); continue; }

    // Detectar heading de capítulo: "CAPÍTULO N:" o línea toda en mayúsculas corta
    if (/^CAPÍTULO\s+\d+[:.]/i.test(t) || /^CHAPTER\s+\d+[:.]/i.test(t)) {
      result.push(heading2(t));
    }
    // Detectar subcapítulo: "1.1", "2.3", etc.
    else if (/^\d+\.\d+[\s.]/.test(t)) {
      result.push(heading3(t));
    }
    // Detectar subtítulos en negrita implícita (línea corta toda mayúsculas)
    else if (t === t.toUpperCase() && t.length < 80 && t.length > 3 && /[A-ZÁÉÍÓÚÑ]/.test(t)) {
      result.push(heading3(t));
    }
    else {
      const p = parrafo(t);
      if (p) result.push(p);
    }
  }
  return result;
}

/** Párrafos de referencias (sangría francesa) */
function referenciasParagrafos(texto) {
  if (!texto) return [];
  const lineas = texto.split('\n');
  const result = [];
  for (const ln of lineas) {
    const t = ln.trim();
    if (!t) { result.push(linea()); continue; }
    const p = parrafoRef(t);
    if (p) result.push(p);
  }
  return result;
}

// ── Construir secciones del documento ────────────────────────────────────────

const children = [];

// ── PORTADA ───────────────────────────────────────────────────────────────────
const centrado = { alignment: AlignmentType.CENTER, spacing: { line: LINE_SPACING } };

children.push(
  new Paragraph({ ...centrado, spacing: { before: 1440, after: 240, line: LINE_SPACING },
    children: [new TextRun({ text: 'MONOGRAFÍA ACADÉMICA', font: FONT, size: SIZE_TITLE, bold: true })] }),
  linea(), linea(),
  new Paragraph({ ...centrado,
    children: [new TextRun({ text: tema.toUpperCase(), font: FONT, size: SIZE_H1, bold: true })] }),
  linea(), linea(), linea(),
  new Paragraph({ ...centrado,
    children: [new TextRun({ text: `Curso: ${curso}`, font: FONT, size: SIZE_BODY })] }),
  new Paragraph({ ...centrado,
    children: [new TextRun({ text: `Especialidad: ${especialidad}`, font: FONT, size: SIZE_BODY })] }),
  new Paragraph({ ...centrado,
    children: [new TextRun({ text: `Nivel: ${nivel}`, font: FONT, size: SIZE_BODY })] }),
  new Paragraph({ ...centrado,
    children: [new TextRun({ text: `Páginas: ${paginas}`, font: FONT, size: SIZE_BODY })] }),
  linea(), linea(),
  new Paragraph({ ...centrado,
    children: [new TextRun({ text: String(anio), font: FONT, size: SIZE_BODY })] }),
  saltoPagina()
);

// ── ÍNDICE (TOC automático) ───────────────────────────────────────────────────
children.push(
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { line: LINE_SPACING, before: 0, after: 480 },
    children: [new TextRun({ text: 'ÍNDICE DE CONTENIDOS', font: FONT, size: SIZE_H1, bold: true })] }),
  new TableOfContents('Tabla de Contenidos', {
    hyperlink: true,
    headingStyleRange: '1-3',
    stylesWithLevels: [
      { styleName: 'Heading 1', level: 1 },
      { styleName: 'Heading 2', level: 2 },
      { styleName: 'Heading 3', level: 3 },
    ]
  }),
  saltoPagina()
);

// ── I. INTRODUCCIÓN ───────────────────────────────────────────────────────────
children.push(heading1('I. Introducción'));
children.push(...textoParagrafos(introduccion));
children.push(saltoPagina());

// ── II. DESARROLLO ────────────────────────────────────────────────────────────
children.push(heading1('II. Desarrollo'));
children.push(...textoParagrafos(desarrollo));
children.push(saltoPagina());

// ── III. CONCLUSIONES Y RECOMENDACIONES ──────────────────────────────────────
children.push(heading1('III. Conclusiones y Recomendaciones'));
children.push(...textoParagrafos(conclusiones));
children.push(saltoPagina());

// ── IV. REFERENCIAS BIBLIOGRÁFICAS ────────────────────────────────────────────
children.push(heading1('IV. Referencias Bibliográficas'));
children.push(
  new Paragraph({ alignment: AlignmentType.LEFT, indent: { left: INDENT_LEFT },
    spacing: { line: LINE_SPACING, after: 240 },
    children: [new TextRun({ text: '(Formato APA 7ma edición — Español, Inglés y Portugués)',
      font: FONT, size: SIZE_BODY, italics: true })] })
);
children.push(...referenciasParagrafos(referencias));

// ── Filtrar nulls ─────────────────────────────────────────────────────────────
const childrenFinal = children.filter(Boolean);

// ── Crear documento ───────────────────────────────────────────────────────────
const doc = new Document({
  styles: {
    default: {
      document: { run: { font: FONT, size: SIZE_BODY } }
    },
    paragraphStyles: [
      {
        id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: SIZE_H1, bold: true, font: FONT, color: '000000' },
        paragraph: { spacing: { before: 480, after: 240, line: LINE_SPACING }, outlineLevel: 0 }
      },
      {
        id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: SIZE_H2, bold: true, font: FONT, color: '000000' },
        paragraph: { spacing: { before: 360, after: 180, line: LINE_SPACING },
          indent: { left: INDENT_LEFT }, outlineLevel: 1 }
      },
      {
        id: 'Heading3', name: 'Heading 3', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: SIZE_BODY, bold: true, italics: true, font: FONT, color: '000000' },
        paragraph: { spacing: { before: 240, after: 120, line: LINE_SPACING },
          indent: { left: INDENT_LEFT }, outlineLevel: 2 }
      },
    ]
  },
  sections: [{
    properties: {
      page: {
        size:   { width: 12240, height: 15840 },   // US Letter
        margin: { top: MARGIN, right: MARGIN, bottom: MARGIN, left: MARGIN }
      },
      pageNumberStart: 1,
    },
    footers: {
      default: new Footer({
        children: [
          new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [
              new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: SIZE_BODY }),
            ]
          })
        ]
      })
    },
    children: childrenFinal,
  }]
});

// ── Guardar ───────────────────────────────────────────────────────────────────
Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync(salida, buffer);
  console.log(`OK:${salida}`);
}).catch(err => {
  console.error('ERROR:', err.message);
  process.exit(1);
});

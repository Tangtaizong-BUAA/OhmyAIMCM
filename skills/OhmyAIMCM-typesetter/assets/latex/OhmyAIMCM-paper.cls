% Deterministic CUMCM paper class.  Keep this file self-contained with the output.
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{OhmyAIMCM-paper}[2026/08/12 v0.1 deterministic CUMCM paper]

\DeclareOption*{\PassOptionsToClass{\CurrentOption}{ctexart}}
\ProcessOptions\relax
\LoadClass[UTF8,fontset=fandol,a4paper,oneside]{ctexart}
\RequirePackage{OhmyAIMCM-style}

% The renderer strips author metadata in anonymous mode.  The class deliberately
% never prints an author, institution, team number, or date.
\renewcommand{\maketitle}{%
  \begingroup
  \thispagestyle{empty}%
  \OhmyAIMCMTitleAlignment
  {\OhmyAIMCMTitleFont\@title\par}%
  \vspace{1.15em}%
  \endgroup
}

\endinput

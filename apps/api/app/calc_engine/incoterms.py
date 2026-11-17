"""Incoterms 2020: which party pays each cost segment. Used to avoid double counting."""

from __future__ import annotations

from enum import StrEnum


class Incoterm(StrEnum):
    EXW = "EXW"
    FCA = "FCA"
    FOB = "FOB"
    CFR = "CFR"
    CIF = "CIF"
    CPT = "CPT"
    CIP = "CIP"
    DAP = "DAP"
    DPU = "DPU"
    DDP = "DDP"


class Segment(StrEnum):
    ORIGIN_INLAND = "origin_inland"  # factory -> port/terminal of export
    EXPORT_CLEARANCE = "export_clearance"
    MAIN_FREIGHT = "main_freight"  # main international carriage
    INSURANCE = "insurance"  # cargo insurance for main carriage
    IMPORT_CLEARANCE = "import_clearance"  # broker / customs formalities at destination
    IMPORT_DUTIES_TAXES = "import_duties_taxes"  # duty + import VAT
    DEST_INLAND = "dest_inland"  # destination port/terminal -> final place


class Party(StrEnum):
    SELLER = "seller"
    BUYER = "buyer"


S, B = Party.SELLER, Party.BUYER
_SEGMENTS = list(Segment)


def _row(*payers: Party) -> dict[Segment, Party]:
    assert len(payers) == len(_SEGMENTS)
    return dict(zip(_SEGMENTS, payers, strict=True))


# Column order = Segment order:
#              origin  export  freight insur.  imp.clr duties  dest
MATRIX: dict[Incoterm, dict[Segment, Party]] = {
    Incoterm.EXW: _row(B, B, B, B, B, B, B),
    Incoterm.FCA: _row(S, S, B, B, B, B, B),
    Incoterm.FOB: _row(S, S, B, B, B, B, B),
    Incoterm.CFR: _row(S, S, S, B, B, B, B),
    Incoterm.CIF: _row(S, S, S, S, B, B, B),
    Incoterm.CPT: _row(S, S, S, B, B, B, B),
    Incoterm.CIP: _row(S, S, S, S, B, B, B),
    Incoterm.DAP: _row(S, S, S, S, B, B, S),
    Incoterm.DPU: _row(S, S, S, S, B, B, S),
    Incoterm.DDP: _row(S, S, S, S, S, S, S),
}

# Costs incurred before the goods reach the destination customs border.
PRE_BORDER: frozenset[Segment] = frozenset(
    {Segment.ORIGIN_INLAND, Segment.EXPORT_CLEARANCE, Segment.MAIN_FREIGHT, Segment.INSURANCE}
)

# Terms whose cost split is fully modelled in the MVP. Others work but get a "review manually" warning
# (e.g. FCA/CPT place of delivery can shift who pays origin inland transport).
FULLY_AUTOMATED: frozenset[Incoterm] = frozenset({Incoterm.EXW, Incoterm.FOB, Incoterm.CIF, Incoterm.DAP, Incoterm.DDP})

# Under these terms the invoice price includes transport beyond the border, so customs value
# computed from the invoice may be overstated (post-border costs are deductible in EU/GCC rules).
POST_BORDER_IN_PRICE: frozenset[Incoterm] = frozenset({Incoterm.DAP, Incoterm.DPU, Incoterm.DDP})


def payer(incoterm: Incoterm, segment: Segment) -> Party:
    return MATRIX[incoterm][segment]

"""Small offline index of conditional exposition moves; never chooses a model."""
import argparse
import json
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "references/exposition-cards.json"


def search(cards, terms, limit=3):
    terms = [t.casefold() for t in terms if t.strip()]
    ranked = []
    for card in cards:
        haystack = " ".join(str(card[k]) for k in ("reader_gap", "move", "conditions", "evidence_needed", "id", "group")).casefold()
        score = sum(t in haystack for t in terms)
        if score:
            ranked.append((score, card))
    ranked.sort(key=lambda item: (-item[0], item[1]["id"]))
    return [card for _, card in ranked[:limit]]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["list", "query", "show", "health"])
    parser.add_argument("terms", nargs="*")
    parser.add_argument("--limit", type=int, default=3)
    args = parser.parse_args()
    cards = json.loads(DATA.read_text())["cards"]
    if args.command == "health":
        ids = [c["id"] for c in cards]
        healthy = bool(cards) and len(ids) == len(set(ids)) and all(
            c.get("sources") and c.get("conditions") and c.get("misuse") and c.get("status") for c in cards)
        print(json.dumps({"healthy": healthy, "cards": len(cards),
                          "scope": "schema and local resource only; no source re-verification or performance certification"}))
        raise SystemExit(0 if healthy else 1)
    if args.command == "list":
        result = [{"id": c["id"], "reader_gap": c["reader_gap"]} for c in cards]
    elif args.command == "show":
        result = [c for c in cards if c["id"] in args.terms]
    else:
        if not args.terms or not 1 <= args.limit <= 18:
            parser.error("query needs space-separated literal keywords and limit 1–18")
        result = search(cards, args.terms, args.limit)
    print(json.dumps({"matches": result, "note": "No match is valid; keep autonomous writing. Search is literal keyword matching, not semantic ranking."}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

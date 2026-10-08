// Prüft den Formatter in derselben JavaScript-Laufzeit wie The Things Stack (goja),
// mit dem Aufruf-Rahmen aus lorawan-stack pkg/messageprocessors/javascript (wrapUplinkDecoderScript).
// Aufruf: go run . <formatter.js> <vektoren.json>
// Copyright (C) 2026 Philipp Schnabel – GPL-3.0-or-later
package main

import (
	"encoding/json"
	"fmt"
	"os"
	"reflect"
	"time"

	"github.com/dop251/goja"
)

// Rahmen wie in The Things Stack v3 (wrapUplinkDecoderScript), gekürzt um normalizeUplink.
const rahmen = `
%s

function main(input) {
	const bytes = input.bytes.slice();
	const { fPort, recvTime } = input;
	const jsDate = new Date(Number(BigInt(recvTime) / 1000000n));
	if (typeof decodeUplink === 'function') {
		return { decoded: decodeUplink({ bytes, fPort, recvTime: jsDate }) };
	}
	return { decoded: { data: Decoder(bytes, fPort) } };
}
`

type eingabe struct {
	Bytes    []uint8 `json:"bytes"`
	FPort    uint8   `json:"fPort"`
	RecvTime int64   `json:"recvTime"`
}

type vektor struct {
	FPort    uint8           `json:"fPort"`
	Bytes    []uint8         `json:"bytes"`
	Erwartet json.RawMessage `json:"erwartet"`
}

func normiere(raw []byte) any {
	var v map[string]any
	if err := json.Unmarshal(raw, &v); err != nil {
		panic(err)
	}
	// Leere Listen wie im Node-Test behandeln
	for _, k := range []string{"warnings", "errors"} {
		if v[k] == nil {
			v[k] = []any{}
		}
	}
	return v
}

func main() {
	if len(os.Args) != 3 {
		fmt.Println("Aufruf: go run . <formatter.js> <vektoren.json>")
		os.Exit(2)
	}
	skript, err := os.ReadFile(os.Args[1])
	if err != nil {
		panic(err)
	}
	prog, err := goja.Compile("", fmt.Sprintf(rahmen, skript), false)
	if err != nil {
		fmt.Println("Übersetzen fehlgeschlagen:", err)
		os.Exit(1)
	}
	var vek []vektor
	raw, err := os.ReadFile(os.Args[2])
	if err != nil {
		panic(err)
	}
	if err := json.Unmarshal(raw, &vek); err != nil {
		panic(err)
	}
	fehler := 0
	for n, v := range vek {
		vm := goja.New()
		vm.SetFieldNameMapper(goja.TagFieldNameMapper("json", true))
		if _, err := vm.RunProgram(prog); err != nil {
			panic(err)
		}
		f, _ := goja.AssertFunction(vm.Get("main"))
		res, err := f(goja.Undefined(), vm.ToValue(eingabe{v.Bytes, v.FPort, time.Now().UnixNano()}))
		if err != nil {
			fmt.Printf("Vektor %d: Laufzeitfehler: %v\n", n, err)
			fehler++
			continue
		}
		out, _ := json.Marshal(res.Export().(map[string]any)["decoded"])
		if !reflect.DeepEqual(normiere(out), normiere(v.Erwartet)) {
			fehler++
			if fehler <= 5 {
				fmt.Printf("Vektor %d (FPort %d, %v):\n  goja: %s\n  node: %s\n", n, v.FPort, v.Bytes, out, v.Erwartet)
			}
		}
	}
	fmt.Printf("goja: %d von %d Vektoren gleich wie Node\n", len(vek)-fehler, len(vek))
	if fehler > 0 {
		os.Exit(1)
	}
}

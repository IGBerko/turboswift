using System;
using System.IO;

class Turbalance
{
    // Простейший "парсер", который на входе получает код TurboSwift,
    // и генерирует Python-функцию check_syntax, которая проверяет простое правило.
    static void Main(string[] args)
    {
        if (args.Length < 2)
        {
            Console.WriteLine("Usage: turbalance.exe <input.ts> <output.py>");
            return;
        }

        string inputFile = args[0];
        string outputFile = args[1];

        string code = File.ReadAllText(inputFile);

        // Простая проверка: есть ли слово "contract"
        bool hasContract = code.Contains("contract");

        using (StreamWriter sw = new StreamWriter(outputFile))
        {
            sw.WriteLine("def check_syntax(code):");
            if (!hasContract)
            {
                sw.WriteLine("    return [\"Missing 'contract' keyword\"]");
            }
            else
            {
                sw.WriteLine("    return []");
            }
        }

        Console.WriteLine($"Generated {outputFile} from {inputFile}");
    }
}

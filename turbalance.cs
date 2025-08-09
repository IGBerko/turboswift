using System;
using System.Collections.Generic;

namespace TurbalanceDebug
{
    public class Turbalance
    {
        // Метод проверки синтаксиса Turbalance
        public List<string> CheckSyntax(string code)
        {
            List<string> errors = new List<string>();
            Stack<int> braceStack = new Stack<int>();
            string[] lines = code.Split(new[] { "\r\n", "\r", "\n" }, StringSplitOptions.None);

            for (int i = 0; i < lines.Length; i++)
            {
                string line = lines[i];
                for (int j = 0; j < line.Length; j++)
                {
                    if (line[j] == '{')
                    {
                        braceStack.Push(i + 1);
                    }
                    else if (line[j] == '}')
                    {
                        if (braceStack.Count == 0)
                        {
                            errors.Add($"[TURBALANCE] Line {i + 1}: Extra '}}'");
                        }
                        else
                        {
                            braceStack.Pop();
                        }
                    }
                }

                string trimmed = line.Trim();
                if (trimmed.StartsWith("contract") && !trimmed.Contains("{"))
                {
                    errors.Add($"[TURBALANCE] Line {i + 1}: Expected '{{' after 'contract'");
                }

                if (trimmed.StartsWith("import") && trimmed.Contains("aka") && !trimmed.EndsWith(";"))
                {
                    errors.Add($"[TURBALANCE] Line {i + 1}: Import statement must end with ';'");
                }

                // Можно добавить другие проверки по необходимости
            }

            while (braceStack.Count > 0)
            {
                int lineNum = braceStack.Pop();
                errors.Add($"[TURBALANCE] Line {lineNum}: Unclosed '{{'");
            }

            return errors;
        }

        // Пример вызова проверки
        public void RunCheck(string code)
        {
            var errors = CheckSyntax(code);
            if (errors.Count == 0)
            {
                Console.WriteLine("No syntax errors found.");
            }
            else
            {
                foreach (var err in errors)
                {
                    Console.WriteLine(err);
                }
            }
        }
    }
}

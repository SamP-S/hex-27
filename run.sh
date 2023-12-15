# debugging
#python Hex.py "a=PNA;python agents/DefaultAgents/NaiveAgent.py" "a=JNA;java -classpath agents/DefaultAgents NaiveAgent" -v
#python Hex.py "a=PNA;python agents/DefaultAgents/NaiveAgent.py" "a=Wolve;python agents/Group27/WolveAgent.py" -v
#python Hex.py "a=PNA;python agents/DefaultAgents/NaiveAgent.py" "a=Electro;python agents/Group27/ElectroAgent.py" -v
#python Hex.py "a=PNA;python agents/DefaultAgents/NaiveAgent.py" "a=Control;python agents/Group27/ControlAgent.py" -v

# testing
STD_IFS=$IFS
IFS=$'\n'

agents=("a=Bob;./agents/TestAgents/bob/bobagent"
        "a=Joni;./agents/TestAgents/joni/joniagent --agent minimax --depth 2 --heuristic monte-carlo --num-playouts 500"
        "a=Alice;./agents/TestAgents/alice/alice"
        "a=Jimmie;python agents/TestAgents/jimmie/Agentjimmie"
        "a=Rita;java -jar agents/TestAgents/rita/rita.jar"
        )


agent_count=5
agent_names=(   "Bob"
                "Joni"
                "Alice"
                "Jimmie"
                "Rita"
            )

echo "Total Agents = ${#agents[@]}"
echo -n > ./docs/tournament.txt

for ((j = 0; j < agent_count; j++)); do

    agent_name="${agent_names[$j]}"
    agent_cfg="${agents[$j]}"
    first_win=0
    second_win=0

    itr=5
    for ((i = 0; i < itr; i++)); do
        # echo $i
        x=($(python Hex.py "a=Electro;python agents/Group27/ControlAgent.py" $agent_cfg -v 2>/dev/null))
        echo "${x[@]}"
        if [[ "${x[-4]}" == *"Electro"* ]]; then
            ((first_win++))
        fi
        y=($(python Hex.py $agent_cfg "a=Electro;python agents/Group27/ControlAgent.py" -v 2>/dev/null))
        echo "${y[@]}"
        if [[ "${y[-4]}" == *"Electro"* ]]; then
            ((second_win++))
        fi
    done
    echo "Electro vs $agent_name"
    echo "$first_win / $itr"
    echo "$agent_name vs Electro"
    echo "$second_win / $itr"
    echo ""

    echo "Electro vs $agent_name" >> ./docs/tournament.txt
    echo "$first_win / $itr" >> ./docs/tournament.txt
    echo "$agent_name vs Electro" >> ./docs/tournament.txt
    echo "$second_win / $itr" >> ./docs/tournament.txt
    echo "" >> ./docs/tournament.txt

done


IFS=$STD_IFS
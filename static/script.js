function showRandomFrom(chosenFile){
	document.getElementsByClassName(chosenFile)[0].innerHTML = chosenArray[Math.floor(Math.random() * chosenArray.length)];
}
package com.armenian.flashcards.ui

import android.animation.AnimatorInflater
import android.animation.AnimatorSet
import android.content.Intent
import android.os.Bundle
import android.view.Menu
import android.view.MenuItem
import android.view.View
import androidx.activity.viewModels
import androidx.appcompat.app.AppCompatActivity
import com.armenian.flashcards.R
import com.armenian.flashcards.databinding.ActivityMainBinding
import com.armenian.flashcards.ui.viewmodel.FlashcardViewModel

/**
 * Main activity for reviewing flashcards with Anki-like interface.
 */
class MainActivity : AppCompatActivity() {
    
    private lateinit var binding: ActivityMainBinding
    private val viewModel: FlashcardViewModel by viewModels()
    
    private var isShowingFront = true
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)
        
        setSupportActionBar(binding.toolbar)
        
        setupObservers()
        setupClickListeners()
    }
    
    private fun setupObservers() {
        viewModel.currentCard.observe(this) { card ->
            if (card != null) {
                binding.flashcardContainer.visibility = View.VISIBLE
                binding.emptyStateLayout.visibility = View.GONE
                
                // Show front of card
                isShowingFront = true
                binding.cardTextView.text = card.frontText
                binding.pronunciationTextView.visibility = View.GONE
                
                // Reset button visibility
                hideRatingButtons()
                binding.showAnswerButton.visibility = View.VISIBLE
            } else {
                binding.flashcardContainer.visibility = View.GONE
                binding.emptyStateLayout.visibility = View.VISIBLE
                hideRatingButtons()
                binding.showAnswerButton.visibility = View.GONE
            }
        }
        
        viewModel.isShowingAnswer.observe(this) { isShowing ->
            if (isShowing && viewModel.currentCard.value != null) {
                showAnswer()
            }
        }
        
        viewModel.currentDeck.observe(this) { deck ->
            deck?.let {
                binding.deckNameTextView.text = it.name
            }
        }
        
        viewModel.newCardsCount.observe(this) { count ->
            binding.newCardsTextView.text = getString(R.string.new_cards_count, count)
        }
        
        viewModel.reviewCardsCount.observe(this) { count ->
            binding.reviewCardsTextView.text = getString(R.string.review_cards_count, count)
        }
    }
    
    private fun setupClickListeners() {
        // Tap card to flip
        binding.flashcardContainer.setOnClickListener {
            if (!viewModel.isShowingAnswer.value!!) {
                viewModel.showAnswer()
            }
        }
        
        // Show answer button
        binding.showAnswerButton.setOnClickListener {
            viewModel.showAnswer()
        }
        
        // Rating buttons
        binding.againButton.setOnClickListener {
            viewModel.rateCard(0)
        }
        
        binding.hardButton.setOnClickListener {
            viewModel.rateCard(1)
        }
        
        binding.goodButton.setOnClickListener {
            viewModel.rateCard(2)
        }
        
        binding.easyButton.setOnClickListener {
            viewModel.rateCard(3)
        }
    }
    
    private fun showAnswer() {
        val card = viewModel.currentCard.value ?: return
        
        // Flip animation
        flipCard()
        
        // Show back of card
        binding.cardTextView.text = card.backText
        
        // Show pronunciation if available
        if (!card.pronunciation.isNullOrEmpty()) {
            binding.pronunciationTextView.text = card.pronunciation
            binding.pronunciationTextView.visibility = View.VISIBLE
        }
        
        // Show rating buttons
        binding.showAnswerButton.visibility = View.GONE
        showRatingButtons()
    }
    
    private fun flipCard() {
        try {
            val scale = applicationContext.resources.displayMetrics.density
            binding.flashcardContainer.cameraDistance = 8000 * scale
            
            val flipOut = AnimatorInflater.loadAnimator(this, R.animator.flip_out) as AnimatorSet
            val flipIn = AnimatorInflater.loadAnimator(this, R.animator.flip_in) as AnimatorSet
            
            flipOut.setTarget(binding.flashcardContainer)
            flipIn.setTarget(binding.flashcardContainer)
            
            flipOut.start()
            flipIn.startDelay = 150
            flipIn.start()
        } catch (e: Exception) {
            // Fallback if animators don't exist - just show the content
            e.printStackTrace()
        }
    }
    
    private fun showRatingButtons() {
        binding.againButton.visibility = View.VISIBLE
        binding.hardButton.visibility = View.VISIBLE
        binding.goodButton.visibility = View.VISIBLE
        binding.easyButton.visibility = View.VISIBLE
    }
    
    private fun hideRatingButtons() {
        binding.againButton.visibility = View.GONE
        binding.hardButton.visibility = View.GONE
        binding.goodButton.visibility = View.GONE
        binding.easyButton.visibility = View.GONE
    }
    
    override fun onCreateOptionsMenu(menu: Menu?): Boolean {
        menuInflater.inflate(R.menu.main_menu, menu)
        return true
    }
    
    override fun onOptionsItemSelected(item: MenuItem): Boolean {
        return when (item.itemId) {
            R.id.action_view_all_cards -> {
                startActivity(Intent(this, CardListActivity::class.java))
                true
            }
            R.id.action_statistics -> {
                // TODO: Implement statistics screen
                true
            }
            R.id.action_settings -> {
                // TODO: Implement settings screen
                true
            }
            else -> super.onOptionsItemSelected(item)
        }
    }
}
